#!/usr/bin/env python3
"""Execute and record the bounded 90 x 24 static review matrix."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
CYCLES = 90
SYNTAX_SUBPROCESS_TIMEOUT_SECONDS = 15
BENCHMARK_SUBPROCESS_TIMEOUT_SECONDS = 30
BENCHMARK_VALIDATION_DIGEST: str | None = None
VISUAL_VALIDATION_DIGESTS: dict[str, str] | None = None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def check_version() -> None:
    version = text("VERSION").strip()
    require(re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version) is not None, "non-canonical VERSION")
    require(f"version: {version}" in text("CITATION.cff"), "CITATION version drift")
    require(version in text("README.md"), "README version drift")
    require(json.loads(text("benchmarks/m5-air-24gb.template.json"))["repository_version"] == version, "benchmark version drift")
    evidence = json.loads(text(f"docs/audit/external-evidence-{version}.json"))
    require(evidence.get("repository_version") == version, "external evidence version drift")
    require(evidence.get("scope_note") and "not a vendored copy" in evidence["scope_note"], "external evidence boundary missing")
    ids = [item.get("id") for item in evidence.get("sources", [])]
    require(len(ids) == len(set(ids)) and len(ids) >= 25, "external evidence inventory is incomplete or duplicated")
    require(all(str(item.get("url", "")).startswith("https://") for item in evidence["sources"]), "external evidence URL is not HTTPS")
    for required_id in ("google-gemma4-model-card", "apple-m5-air-13", "apple-m5-air-15", "lmstudio-authentication", "lmstudio-parallel-requests", "lmstudio-rest-api"):
        require(required_id in ids, f"external evidence missing: {required_id}")
    ledger = json.loads(text(f"docs/audit/revision-ledger-{version}.json"))
    require(ledger.get("repository_version") == version, "revision ledger version drift")
    require(ledger.get("summary", {}).get("critical_findings_remaining") == 0, "revision ledger has unresolved critical findings")
    require(ledger.get("summary", {}).get("revisions_recorded", 0) >= 104, "revision ledger is incomplete")



def evidence_by_id() -> dict[str, dict[str, object]]:
    version = text("VERSION").strip()
    record = json.loads(text(f"docs/audit/external-evidence-{version}.json"))
    return {str(item["id"]): item for item in record["sources"]}


def check_configuration_grammar() -> None:
    common = text("scripts/lib/common.sh")
    for token in ("validate_config_files", "unsupported configuration key", "duplicate configuration key", "group/world-writable", "LF line endings"):
        require(token in common, f"strict configuration grammar missing: {token}")
    completed = subprocess.run(
        ["bash", "-c", "source scripts/lib/common.sh; validate_config_files"], cwd=ROOT,
        check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20,
    )
    require(completed.returncode == 0, f"canonical configuration rejected: {completed.stderr.strip()}")


def check_ci_action_pins() -> None:
    workflow = text(".github/workflows/ci.yml")
    expected = {
        "github-actions-checkout": ("actions/checkout", "3d3c42e5aac5ba805825da76410c181273ba90b1", "v7.0.1"),
        "github-actions-setup-python": ("actions/setup-python", "5fda3b95a4ea91299a34e894583c3862153e4b97", "v7.0.0"),
    }
    sources = evidence_by_id()
    for source_id, (action, commit, release) in expected.items():
        require(f"{action}@{commit} # {release}" in workflow, f"immutable action pin missing: {action}")
        require(sources[source_id].get("immutable_commit") == commit, f"action evidence commit drift: {source_id}")
    require(re.search(r"actions/(?:checkout|setup-python)@v\\d+", workflow) is None, "floating action major tag found")


def check_primary_source_contract() -> None:
    sources = evidence_by_id()
    expected_urls = {
        "apple-macbook-air-identification": "https://support.apple.com/en-us/102869",
        "apple-m5-air-13": "https://support.apple.com/en-us/126320",
        "apple-m5-air-15": "https://support.apple.com/en-us/126321",
        "lmstudio-gemma4-family": "https://lmstudio.ai/models/gemma-4",
        "lmstudio-parallel-requests": "https://lmstudio.ai/docs/app/advanced/parallel-requests",
        "lmstudio-cli-load-source": "https://github.com/lmstudio-ai/lms/blob/71bd99ccf882a0410cfd574ee220a99083608930/src/subcommands/load.ts",
        "lmstudio-0.4.20-changelog": "https://lmstudio.ai/changelog/lmstudio-v0.4.20",
        "lmstudio-system-requirements": "https://lmstudio.ai/docs/app/system-requirements",
    }
    for source_id, url in expected_urls.items():
        require(sources.get(source_id, {}).get("url") == url, f"primary source URL drift: {source_id}")

def load_resolver():
    path = ROOT / "scripts/resolve_model_identity.py"
    spec = importlib.util.spec_from_file_location("matrix_resolver", path)
    require(spec is not None and spec.loader is not None, "resolver import failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check_exact_model() -> None:
    module = load_resolver()
    valid = {"models": [{"modelKey": "google/gemma-4-26b-a4b-qat@q4_0", "path": "google/gemma-4-26b-a4b-qat/model-Q4_0.gguf", "displayName": "Gemma 4 26B A4B QAT Q4_0", "format": "gguf", "deviceIdentifier": None}]}
    lookalike = {"models": [{"modelKey": "third-party/gemma-4-26b-a4b-qat@q4_0", "path": "third-party/gemma-4-26b-a4b-qat/model-Q4_0.gguf", "displayName": "Gemma 4 26B A4B QAT Q4_0", "format": "gguf", "deviceIdentifier": None}]}
    require(len(module.choose_identities(valid)) == 1, "exact Google identity rejected")
    require(module.choose_identities(lookalike) == [], "lookalike catalog identity accepted")


def check_lm_contract() -> None:
    defaults = text("config/defaults.conf")
    require("MIN_LM_STUDIO_VERSION=0.4.11" in defaults, "LM Studio minimum drift")
    require("RECOMMENDED_LM_STUDIO_VERSION=0.4.20" in defaults, "LM Studio recommendation drift")
    contract = text("scripts/verify_lms_cli_contract.sh")
    for token in ("lms get", "lms load", "lms ls", "lms ps", "lms server"):
        require(token in contract, f"missing CLI capability: {token}")
    require("lms unload" in text("scripts/load_model.sh") and "lms unload" in text("scripts/stop_server.sh"), "unload capability path missing")


def check_hardware() -> None:
    defaults = text("config/defaults.conf")
    for token in ("TARGET_MODEL_NAME=MacBook Air", "TARGET_CHIP_TOKEN=M5", "TARGET_MODEL_IDENTIFIERS=Mac17,3,Mac17,4", "MIN_MEMORY_GB=24", "MIN_MACOS_VERSION=26.0", "CONTEXT_LENGTH=8192", "MAX_CONCURRENT_PREDICTIONS=1"):
        require(token in defaults, f"hardware profile drift: {token}")


def check_model_state() -> None:
    loader = text("scripts/load_model.sh")
    verifier = text("scripts/verify_loaded_model.py")
    for token in ("--phase pre", "--phase post", "trap cleanup_failed_load EXIT", "lms unload \"$identifier\"", "--parallel \"$parallel\""):
        require(token in loader, f"load invariant missing: {token}")
    for token in ("already-loaded", "conflict", "expected-model-path", "expected-model-key", "expected-parallel"):
        require(token in verifier, f"postcondition invariant missing: {token}")


def check_api() -> None:
    require("REQUIRE_API_AUTH=1" in text("config/defaults.conf"), "API auth not fixed")
    start = text("scripts/start_server.sh")
    for token in ("127.0.0.1", "verify_api_auth.sh", "assert_loopback_listener", "cleanup_failed_start"):
        require(token in start, f"server invariant missing: {token}")
    policy = text("scripts/api_url_policy.py")
    require("allow_remote" in policy and "https" in policy and "loopback" in policy.lower(), "endpoint policy incomplete")


def check_tools_mcp() -> None:
    tool = text("examples/safe_tool_call.py")
    mcp = text("examples/mcp_request.sh")
    require("validate_memory_pressure_call" in tool and "[/usr/bin/memory_pressure" not in tool, "tool validator missing")
    require("['/usr/bin/memory_pressure', '-Q']" in tool and "shell=True" not in tool, "tool command is not fixed and shell-free")
    require("allowed_tools" in mcp and "MODEL_IDENTIFIER" in mcp and "ephemeral_mcp" in mcp, "MCP allowlist/model override missing")


def check_ssh_git() -> None:
    guide = text("docs/ru/INSTALL_GITHUB_SSH.md")
    checker = text("scripts/check_github_ssh.sh")
    publisher = text("scripts/publish_repository.sh")
    for token in ("github-gendalf71", "ssh-add -l", "config.backup", "Hi Gendalf71!"):
        require(token in guide, f"SSH guide missing: {token}")
    require("ssh -G" in checker and "IdentitiesOnly".lower() in checker.lower(), "SSH effective-config gate missing")
    for token in ("verify_github_known_hosts.sh", "BatchMode=yes", "StrictHostKeyChecking=yes", "ConnectTimeout=15"):
        require(token in checker, f"SSH authentication hardening missing: {token}")
    require("validate_git_identity.py" in publisher, "Git identity validator missing from publication")
    require("git config --local --get user.name" in publisher and "git config --local --get user.email" in publisher, "local Git identity gate missing")


def check_github_metadata() -> None:
    publisher = text("scripts/publish_repository.sh")
    for token in ("Gendalf71", "GemmaM5-1-FullStack", "No model weights included.", "moe", "metal", "local-ai", "openai-compatible", "--default-branch main", "--expected-visibility public"):
        require(token in publisher, f"GitHub metadata/postcondition missing: {token}")


def check_bilingual_docs() -> None:
    version = text("VERSION").strip()
    pairs = ("INSTALL_MODEL.md", "INSTALL_GITHUB_SSH.md", "COMPATIBILITY.md", "RELEASE.md", "SCREENSHOTS.md", "FINAL_AUDIT.md")
    for name in pairs:
        require((ROOT / "docs" / name).is_file(), f"missing English doc: {name}")
        require((ROOT / "docs/ru" / name).is_file(), f"missing Russian doc: {name}")
    for relative in ("docs/INSTALL_MODEL.md", "docs/ru/INSTALL_MODEL.md", "docs/INSTALL_GITHUB_SSH.md", "docs/ru/INSTALL_GITHUB_SSH.md"):
        require(version in text(relative), f"current version missing: {relative}")


def check_syntax() -> None:
    for path in [*ROOT.glob("scripts/*.py"), *ROOT.glob("examples/*.py"), *ROOT.glob("tests/*.py")]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in [*ROOT.glob("scripts/*.sh"), *ROOT.glob("scripts/lib/*.sh"), *ROOT.glob("examples/*.sh")]:
        try:
            completed = subprocess.run(
                ["bash", "-n", str(path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=SYNTAX_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise AssertionError(f"Bash syntax check timed out after {exc.timeout}s: {path}") from exc
        require(completed.returncode == 0, f"Bash syntax failed: {path}: {completed.stderr.strip()}")
    for path in ROOT.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def check_benchmark() -> None:
    global BENCHMARK_VALIDATION_DIGEST
    benchmark_path = ROOT / "benchmarks/m5-air-24gb.template.json"
    current_digest = hashlib.sha256(benchmark_path.read_bytes()).hexdigest()
    if BENCHMARK_VALIDATION_DIGEST != current_digest:
        try:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_benchmark.py"), str(benchmark_path), "--expected-repository-version", text("VERSION").strip()],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=BENCHMARK_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise AssertionError(f"benchmark validation timed out after {exc.timeout}s") from exc
        require(completed.returncode == 0, f"benchmark schema failed: {completed.stderr.strip()}")
        BENCHMARK_VALIDATION_DIGEST = current_digest
    require(hashlib.sha256(benchmark_path.read_bytes()).hexdigest() == BENCHMARK_VALIDATION_DIGEST, "benchmark changed after validation")
    template = json.loads(text("benchmarks/m5-air-24gb.template.json"))
    require(template["status"] == "not_measured", "benchmark template invents measurement")
    require("macos_build" in template["software"] and "thermal_state" in template["performance"], "benchmark evidence fields incomplete")
    require(set(("profile_id", "run_count", "prompt_sha256", "cold_start")) <= set(template["protocol"]), "benchmark protocol fields incomplete")
    require("prefill_tokens_per_second" in template["performance"] and "decode_tokens_per_second" in template["performance"], "disaggregated performance fields missing")


def parse_manifest() -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in text("SHA256SUMS").splitlines():
        digest, relative = line.split("  ", 1)
        entries.append((digest, relative))
    require([relative for _, relative in entries] == sorted((relative for _, relative in entries), key=lambda value: value.encode()), "manifest is not bytewise sorted")
    return entries


def check_manifest() -> None:
    for expected, relative in parse_manifest():
        path = ROOT / relative
        require(path.is_file(), f"manifest path missing: {relative}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"checksum mismatch: {relative}")


def check_release_builder() -> None:
    builder = text("scripts/build_release.sh")
    zipper = text("scripts/create_release_zip.py")
    for token in ("cmp -s", "unzip -t", "./scripts/verify_repo.sh", "SHA256SUMS", "validate_release_zip.py", "validate_checksum_sidecar.py"):
        require(token in builder, f"release builder gate missing: {token}")
    require("zipfile.ZIP_STORED" in zipper and "FIXED_ZIP_TIME" in zipper, "deterministic ZIP contract missing")
    for path in [*ROOT.glob("scripts/*.sh"), *ROOT.glob("scripts/*.py"), *ROOT.glob("examples/*.sh"), *ROOT.glob("examples/*.py")]:
        require(os.access(path, os.X_OK), f"entry point is not executable: {path}")


def check_visual_and_acceptance_surfaces() -> None:
    global VISUAL_VALIDATION_DIGESTS
    manifest_path = ROOT / "docs/assets/assets-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("repository_version") == text("VERSION").strip(), "asset manifest version drift")
    paths = [ROOT / item["path"] for item in manifest.get("assets", [])]
    current = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in [manifest_path, *paths]}
    if VISUAL_VALIDATION_DIGESTS != current:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/validate_png_assets.py"), str(manifest_path)], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        require(completed.returncode == 0, f"visual asset validation failed: {completed.stderr.strip()}")
        VISUAL_VALIDATION_DIGESTS = current
    require(current == VISUAL_VALIDATION_DIGESTS, "visual asset changed after validation")
    fullstack = text("examples/fullstack_acceptance.py")
    for token in ("MAX_DOCUMENT_BYTES", "MAX_IMAGE_BYTES", "validate_memory_pressure_call", "fixed_memory_pressure", "allow-remote-base-url"):
        require(token in fullstack, f"full-stack boundary missing: {token}")
    require("shell=True" not in fullstack, "full-stack example enables shell execution")
    hardware = text("scripts/capture_hardware_report.sh")
    require("umask 077" in hardware and "chmod 600" in hardware and "review and redact" in hardware, "owner hardware report boundary incomplete")


def check_clean_tree_contract() -> None:
    forbidden = {".gguf", ".safetensors", ".mlmodelc"}
    require(not any(path.is_file() and path.suffix.lower() in forbidden for path in ROOT.rglob("*")), "model weights bundled")
    require("__pycache__" not in text("REPOSITORY_TREE.txt") + text("SHA256SUMS"), "transient path in release inventory")
    verify = text("scripts/verify_repo.sh")
    builder = text("scripts/build_release.sh")
    require("run_repository_test_shards.sh" in verify, "bounded test shards not in final verification")
    require("cd \"$extracted\"" in builder and "./scripts/verify_repo.sh" in builder, "clean-extraction rerun missing")



def check_runtime_release_boundary() -> None:
    defaults = text("config/defaults.conf")
    require("MIN_LM_STUDIO_VERSION=0.4.11" in defaults, "minimum runtime boundary drift")
    require("RECOMMENDED_LM_STUDIO_VERSION=0.4.20" in defaults, "recommended runtime boundary drift")
    compatibility = text("docs/COMPATIBILITY.md")
    require("system-requirements page currently names M1/M2/M3/M4, not M5" in compatibility, "M5 documentation-lag boundary missing")
    sources = evidence_by_id()
    require(sources["lmstudio-0.4.20-changelog"]["url"].endswith("lmstudio-v0.4.20"), "runtime release source drift")


def check_publication_readiness() -> None:
    readme = text("README.md")
    for token in ("Publication status", "Owner acceptance", "measured-versus-unmeasured", "No model weights included"):
        require(token in readme or token.lower() in readme.lower(), f"cold-pitch surface missing: {token}")
    for relative in ("AGENTS.md", "docs/ACCEPTANCE_CHECKLIST.md", "docs/ru/ACCEPTANCE_CHECKLIST.md", "docs/GITHUB_METADATA.md", "docs/ru/GITHUB_METADATA.md", "docs/THREAT_MODEL.md", "docs/ru/THREAT_MODEL.md", "docs/DEPENDENCY_POLICY.md", "docs/ru/DEPENDENCY_POLICY.md", "SUPPORT.md", ".github/ISSUE_TEMPLATE/feature_request.yml"):
        require((ROOT / relative).is_file(), f"publication surface missing: {relative}")
    assurance_source = text("scripts/validate_release_assurance.py")
    for token in ("revision_count", "external_source_count", "unit_tests_expected", "state_digest_sha256"):
        require(token in assurance_source, f"assurance cross-link missing: {token}")


def check_text_quality() -> None:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts/verify_text_quality.py")], cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    require(completed.returncode == 0, f"text quality failed: {completed.stderr.strip()}")
    source = text("scripts/verify_repo.sh")
    require("compileall" not in source, "bytecode-producing compileall remains in verification")
    require("verify_text_quality.py" in source, "independent text-quality gate missing")


def check_authenticated_examples() -> None:
    policy = text("scripts/api_url_policy.py")
    require("def require_api_token" in policy, "API token validator missing")
    for relative in ("examples/text_request.py", "examples/vision_request.py", "examples/safe_tool_call.py", "examples/fullstack_acceptance.py", "tests/api_smoke_test.py"):
        source = text(relative)
        require("require_api_token" in source, f"authenticated API client boundary missing: {relative}")
        require("Authorization" in source, f"authorization header missing: {relative}")


def check_image_input_policy() -> None:
    source = text("scripts/image_policy.py")
    for token in ("MAX_IMAGE_BYTES", "PNG", "JPEG", "WebP", "Image is empty"):
        require(token in source, f"image policy missing: {token}")
    for relative in ("examples/vision_request.py", "examples/fullstack_acceptance.py", "tests/api_smoke_test.py"):
        require("image_data_url" in text(relative), f"shared image policy not used: {relative}")


def check_explicit_runtime_upgrade() -> None:
    installer = text("scripts/install_lm_studio.sh")
    require("--upgrade" in installer, "explicit upgrade flag missing")
    require("No implicit upgrade was performed" in installer, "no-upgrade default is not documented")
    require("brew upgrade --cask lm-studio" in installer, "explicit upgrade path missing")
    require("RECOMMENDED_LM_STUDIO_VERSION=0.4.20" in text("config/defaults.conf"), "runtime recommendation drift")

DOMAINS: list[tuple[str, Callable[[], None]]] = [
    ("canonical_version", check_version),
    ("exact_google_catalog_identity", check_exact_model),
    ("lm_studio_cli_contract", check_lm_contract),
    ("target_hardware_and_memory", check_hardware),
    ("model_state_and_rollback", check_model_state),
    ("localhost_api_and_auth", check_api),
    ("tool_and_mcp_boundaries", check_tools_mcp),
    ("ssh_and_local_git_identity", check_ssh_git),
    ("github_metadata_postconditions", check_github_metadata),
    ("bilingual_operational_docs", check_bilingual_docs),
    ("bash_python_json_syntax", check_syntax),
    ("benchmark_evidence_schema", check_benchmark),
    ("manifest_and_sha256", check_manifest),
    ("deterministic_release_contract", check_release_builder),
    ("clean_tree_and_extraction_contract", lambda: (check_visual_and_acceptance_surfaces(), check_clean_tree_contract())),
    ("strict_configuration_grammar", check_configuration_grammar),
    ("immutable_ci_action_pins", check_ci_action_pins),
    ("exact_primary_source_contract", check_primary_source_contract),
    ("current_runtime_release_boundary", check_runtime_release_boundary),
    ("cold_pitch_publication_readiness", check_publication_readiness),
    ("independent_text_quality", check_text_quality),
    ("authenticated_api_examples", check_authenticated_examples),
    ("validated_image_inputs", check_image_input_policy),
    ("explicit_runtime_upgrade", check_explicit_runtime_upgrade),
]


def repository_state_digest() -> str:
    """Hash the audited state while excluding self-referential generated records."""
    version = text("VERSION").strip()
    excluded = {
        "SHA256SUMS",
        f"docs/audit/iteration-matrix-{version}.json",
        f"docs/audit/release-assurance-{version}.json",
    }
    digest = hashlib.sha256()
    for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix().encode()):
        relative = path.relative_to(ROOT).as_posix()
        if relative in excluded or "__pycache__" in path.parts or relative.startswith(("dist/", "artifacts/", ".git/")) or relative == ".git" or "/.git/" in ("/" + relative + "/"):
            continue
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def execute() -> dict[str, object]:
    passes: list[dict[str, object]] = []
    # Cycle 1 executes every complete domain validator. Later cycles prove that
    # the audited repository state has not changed and carry forward only that
    # already-established domain result. This avoids pretending that 1,200
    # expensive subprocess runs are independent reviews.
    for domain_index, (name, function) in enumerate(DOMAINS, 1):
        function()
        passes.append({"outer_cycle": 1, "domain_index": domain_index, "domain": name, "status": "passed", "mode": "full-validator"})
    baseline_digest = repository_state_digest()
    for outer in range(2, CYCLES + 1):
        require(repository_state_digest() == baseline_digest, f"repository state drift before cycle {outer}")
        for domain_index, (name, _) in enumerate(DOMAINS, 1):
            passes.append({"outer_cycle": outer, "domain_index": domain_index, "domain": name, "status": "passed", "mode": "state-integrity-recheck"})
    return {
        "schema_version": 2,
        "repository_version": text("VERSION").strip(),
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "outer_cycles": CYCLES,
        "domains_per_cycle": len(DOMAINS),
        "total_control_passes": len(passes),
        "state_digest_sha256": baseline_digest,
        "scope_note": "Cycle 1 executes all full validators. Cycles 2-90 repeat repository-state integrity checks and carry forward the established domain closure; these are not independent human reviews or hardware benchmarks.",
        "passes": passes,
        "summary": {"passed": len(passes), "failed": 0, "critical_findings_remaining": 0},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    result = execute()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded {result['total_control_passes']} static control passes: {args.output}")
        return 0
    try:
        recorded = json.loads(args.verify.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read matrix record: {exc}", file=sys.stderr)
        return 1
    for key in ("schema_version", "repository_version", "outer_cycles", "domains_per_cycle", "total_control_passes", "state_digest_sha256", "scope_note", "passes", "summary"):
        require(recorded.get(key) == result.get(key), f"matrix record drift: {key}")
    print(f"Verified {result['total_control_passes']} static control passes against {args.verify}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
