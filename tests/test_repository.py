import json
import importlib.util
import os
import re
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
MATRIX_RELATIVE = f'docs/audit/iteration-matrix-{VERSION}.json'
EVIDENCE_RELATIVE = f'docs/audit/external-evidence-{VERSION}.json'
REVISION_LEDGER_RELATIVE = f'docs/audit/revision-ledger-{VERSION}.json'
ASSURANCE_RELATIVE = f'docs/audit/release-assurance-{VERSION}.json'


class RepositoryTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            'README.md', 'LICENSE', 'SECURITY.md', 'CODE_OF_CONDUCT.md', 'AGENTS.md',
            'CITATION.cff', '.github/dependabot.yml', 'config/defaults.conf',
            'scripts/preflight.sh', 'scripts/parse_hardware_profile.py', 'scripts/validate_benchmark.py', 'scripts/validate_git_identity.py', 'scripts/validate_checksum_sidecar.py', 'scripts/verify_version_references.py', 'scripts/load_model.sh',
            'scripts/publish_repository.sh', 'scripts/collect_environment.sh',
            'scripts/capture_model_provenance.sh', 'scripts/write_model_provenance.py',
            'scripts/build_release.sh', 'scripts/create_release_zip.py', 'scripts/validate_release_zip.py',
            'scripts/stage_release_files.sh', 'scripts/verify_git_inventory.sh',
            'scripts/validate_manifest.py', 'scripts/api_url_policy.py', 'scripts/resolve_model_identity.py', 'scripts/verify_loaded_model.py', 'scripts/check_lm_studio_version.sh', 'scripts/verify_lms_cli_contract.sh',
            'scripts/create_github_release.sh', 'scripts/verify_github_known_hosts.sh', 'scripts/verify_github_release.py', 'scripts/verify_github_repository.py', 'scripts/verify_api_auth.sh', 'scripts/run_repository_tests.py', 'scripts/run_repository_test_shards.sh', 'scripts/generate_iteration_matrix.py',
            'docs/INSTALL_MODEL.md', 'docs/INSTALL_GITHUB_SSH.md', 'docs/COMPATIBILITY.md', 'docs/FINAL_AUDIT.md', MATRIX_RELATIVE, EVIDENCE_RELATIVE, REVISION_LEDGER_RELATIVE, ASSURANCE_RELATIVE,
            'docs/MODEL_PROVENANCE.md', 'docs/TURBO_FIELDFARE_COMPARISON.md', 'docs/ASSURANCE_CASE.md',
            'docs/RELEASE.md', 'docs/SCREENSHOTS.md',
            'docs/ru/README.md', 'docs/ru/RELEASE.md', 'docs/ru/SCREENSHOTS.md',
            'docs/ru/MODEL_PROVENANCE.md', 'docs/ru/TURBO_FIELDFARE_COMPARISON.md', 'docs/ru/ASSURANCE_CASE.md',
            'docs/ru/MCP_SAFE_PATTERNS.md', 'docs/ACCEPTANCE_CHECKLIST.md', 'docs/ru/ACCEPTANCE_CHECKLIST.md', 'docs/GITHUB_METADATA.md', 'docs/ru/GITHUB_METADATA.md', 'docs/THREAT_MODEL.md', 'docs/ru/THREAT_MODEL.md', 'SUPPORT.md',
            'docs/ru/INSTALL_MODEL.md', 'docs/ru/INSTALL_GITHUB_SSH.md', 'docs/ru/COMPATIBILITY.md', 'docs/ru/FINAL_AUDIT.md', 'docs/DEPENDENCY_POLICY.md', 'docs/ru/DEPENDENCY_POLICY.md', '.github/ISSUE_TEMPLATE/feature_request.yml',
            'docs/assets/banner.png', 'docs/assets/assets-manifest.json', 'docs/screenshot-manifest.template.json', 'docs/assets/screenshots/README.md',
            'docs/BENCHMARK_PROTOCOL.md', 'docs/BACKEND_PORTABILITY.md', 'docs/ru/BENCHMARK_PROTOCOL.md', 'docs/ru/BACKEND_PORTABILITY.md',
            'scripts/validate_png_assets.py', 'scripts/verify_text_quality.py', 'scripts/image_policy.py', 'scripts/capture_hardware_report.sh', 'scripts/verify_external_sources.py', 'scripts/validate_release_assurance.py', 'examples/fullstack_acceptance.py',
            'tests/fixtures/vision_test.png', 'tests/fixtures/document_test.md',
            'benchmarks/m5-air-24gb.template.json',
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_iteration_matrix_is_machine_readable_and_complete(self):
        record = json.loads((ROOT / MATRIX_RELATIVE).read_text(encoding='utf-8'))
        self.assertEqual(90, record['outer_cycles'])
        self.assertEqual(24, record['domains_per_cycle'])
        self.assertEqual(2160, record['total_control_passes'])
        self.assertEqual({'passed': 2160, 'failed': 0, 'critical_findings_remaining': 0}, record['summary'])
        self.assertIn('not independent human reviews', record['scope_note'])

    def test_revision_ledger_records_sequential_zero_critical_corrections(self):
        ledger = json.loads((ROOT / REVISION_LEDGER_RELATIVE).read_text(encoding='utf-8'))
        self.assertEqual(VERSION, ledger['repository_version'])
        self.assertEqual('1.1.46', ledger['baseline_version'])
        self.assertEqual('1.1.240', ledger['target_version'])
        versions = [item['version'] for item in ledger['revisions']]
        self.assertEqual([f'1.1.{value}' for value in range(47, 241)], versions)
        self.assertEqual(1, ledger['revisions'][24]['critical_findings_remaining_after_revision'])
        self.assertEqual(0, ledger['revisions'][-1]['critical_findings_remaining_after_revision'])
        self.assertEqual(0, ledger['summary']['critical_findings_remaining'])
        self.assertEqual(0, ledger['summary']['hardware_benchmarks_claimed'])

    def test_external_evidence_record_is_versioned_and_bounded(self):
        evidence = json.loads((ROOT / EVIDENCE_RELATIVE).read_text(encoding='utf-8'))
        self.assertEqual(VERSION, evidence['repository_version'])
        self.assertIn('not a vendored copy', evidence['scope_note'])
        ids = [item['id'] for item in evidence['sources']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 16)
        self.assertTrue(all(item['url'].startswith('https://') for item in evidence['sources']))
        self.assertIn('github-host-fingerprints', ids)
        self.assertIn('lmstudio-target-model', ids)
        by_id = {item['id']: item for item in evidence['sources']}
        self.assertEqual('https://support.apple.com/en-us/126320', by_id['apple-m5-air-13']['url'])
        self.assertEqual('https://support.apple.com/en-us/126321', by_id['apple-m5-air-15']['url'])
        self.assertEqual('https://lmstudio.ai/models/gemma-4', by_id['lmstudio-gemma4-family']['url'])
        self.assertEqual('https://lmstudio.ai/docs/app/advanced/parallel-requests', by_id['lmstudio-parallel-requests']['url'])
        self.assertEqual('3d3c42e5aac5ba805825da76410c181273ba90b1', by_id['github-actions-checkout']['immutable_commit'])
        self.assertEqual('5fda3b95a4ea91299a34e894583c3862153e4b97', by_id['github-actions-setup-python']['immutable_commit'])

    def test_no_model_weights_are_bundled(self):
        forbidden = {'.gguf', '.safetensors', '.bin', '.mlmodelc'}
        offenders = [p for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in forbidden]
        self.assertEqual([], offenders)

    def test_repository_test_runner_is_individually_bounded(self):
        runner = ROOT / 'scripts/run_repository_tests.py'
        self.assertTrue(runner.exists())
        self.assertTrue(os.access(runner, os.X_OK))
        source = runner.read_text(encoding='utf-8')
        self.assertIn('start_new_session=True', source)
        self.assertIn('PYTHONDONTWRITEBYTECODE', source)
        self.assertIn('process.communicate(timeout=timeout)', source)
        self.assertIn('os.killpg(process.pid, signal.SIGKILL)', source)
        self.assertIn('subprocess.TimeoutExpired', source)
        self.assertIn('--from-index', source)
        self.assertIn('--to-index', source)
        self.assertIn('--jobs', source)
        self.assertIn('--batch-size', source)
        self.assertIn('ThreadPoolExecutor', source)
        self.assertNotIn('test.run(result)', source)
        shard_runner = (ROOT / 'scripts/run_repository_test_shards.sh').read_text(encoding='utf-8')
        self.assertIn('discover_test_ids', shard_runner)
        self.assertIn('--from-index', shard_runner)
        self.assertIn('--to-index', shard_runner)
        verify = (ROOT / 'scripts/verify_repo.sh').read_text(encoding='utf-8')
        self.assertIn('run_repository_test_shards.sh"', verify)
        self.assertIn('read_release_version()', (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8'))
        self.assertNotIn("unittest discover -s tests", verify)

    def test_json_files_parse(self):
        for path in ROOT.rglob('*.json'):
            json.loads(path.read_text(encoding='utf-8'))

    def test_shell_scripts_have_shebang(self):
        for path in list((ROOT / 'scripts').rglob('*.sh')) + list((ROOT / 'examples').rglob('*.sh')):
            self.assertTrue(path.read_text(encoding='utf-8').startswith('#!/usr/bin/env bash'), path)

    def test_server_is_explicitly_local(self):
        text = (ROOT / 'scripts/start_server.sh').read_text(encoding='utf-8')
        self.assertIn('--bind "$host"', text)
        self.assertIn('assert_lms_server_status "$port"', text)
        self.assertIn('assert_loopback_listener', text)
        self.assertIn("grep -q -- '--bind'", text)
        self.assertIn('[ "$host" = "127.0.0.1" ]', text)
        for path in (ROOT / 'scripts').rglob('*.sh'):
            body = path.read_text(encoding='utf-8')
            self.assertNotIn('0.0.0.0', body, path)
            self.assertNotIn('--cors', body, path)

    def test_publish_is_dry_run_and_checks_account(self):
        text = (ROOT / 'scripts/publish_repository.sh').read_text(encoding='utf-8')
        self.assertIn('execute=0', text)
        self.assertIn('--execute', text)
        self.assertIn('gh api user --jq .login', text)
        self.assertIn('check_github_ssh.sh"', text)
        self.assertIn('"$host_alias" "$owner"', text)
        self.assertIn('verify_git_inventory.sh" --require-clean', text)
        self.assertIn('gh repo edit', text)
        self.assertIn('Dry run completed. Static repository verification passed.', text)
        self.assertIn('nameWithOwner,visibility,isArchived,description,defaultBranchRef', text)
        self.assertIn('verify_github_repository.py', text)
        self.assertIn('repositoryTopics', text)
        self.assertIn('--expected-topic', text)
        self.assertNotIn('--private', text)
        self.assertNotIn('git config --global', text)

    def test_github_known_hosts_verifier_is_pinned_and_fail_closed(self):
        verifier = (ROOT / 'scripts/verify_github_known_hosts.sh').read_text(encoding='utf-8')
        self.assertIn('SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU', verifier)
        self.assertIn('ssh-keygen -F', verifier)
        self.assertIn('ssh-keygen -lf', verifier)
        self.assertIn('Do not populate it from unauthenticated ssh-keyscan output alone', verifier)
        self.assertNotIn('StrictHostKeyChecking=no', verifier)

    def test_ssh_check_requires_exact_login(self):
        text = (ROOT / 'scripts/check_github_ssh.sh').read_text(encoding='utf-8')
        self.assertIn('Hi ${expected_login}!', text)
        self.assertIn('successfully authenticated', text)
        self.assertIn('verify_github_known_hosts.sh', text)
        self.assertIn('BatchMode=yes', text)
        self.assertIn('StrictHostKeyChecking=yes', text)
        self.assertIn('ConnectTimeout=15', text)
        self.assertNotIn('StrictHostKeyChecking=no', text)
        self.assertIn('ssh -G', text)
        self.assertIn('identitiesonly', text)
        self.assertIn('proxycommand', text)
        self.assertIn('expected SSH IdentityFile', text)

    def test_exact_m5_air_hardware_profile_is_enforced(self):
        defaults = (ROOT / 'config/defaults.conf').read_text(encoding='utf-8')
        preflight = (ROOT / 'scripts/preflight.sh').read_text(encoding='utf-8')
        self.assertIn('TARGET_MODEL_NAME=MacBook Air', defaults)
        self.assertIn('TARGET_CHIP_TOKEN=M5', defaults)
        self.assertIn('MIN_MACOS_VERSION=26.0', defaults)
        self.assertIn('TARGET_MODEL_IDENTIFIERS=Mac17,3,Mac17,4', defaults)
        self.assertIn('system_profiler SPHardwareDataType -json', preflight)
        self.assertIn('Target model must be', preflight)
        self.assertIn('Target chip must contain', preflight)
        self.assertIn('version_at_least', preflight)
        parser = ROOT / 'scripts/parse_hardware_profile.py'
        sample = {'SPHardwareDataType': [{'machine_name': 'MacBook Air', 'machine_model': 'Mac17,3', 'chip_type': 'Apple M5'}]}
        result = subprocess.run([str(parser)], input=json.dumps(sample), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({'model_name': 'MacBook Air', 'model_identifier': 'Mac17,3', 'chip': 'Apple M5'}, json.loads(result.stdout))

    def test_local_configuration_cannot_weaken_secure_target_profile(self):
        common = ROOT / 'scripts/lib/common.sh'
        source = common.read_text(encoding='utf-8')
        self.assertIn('require_secure_target_profile_config()', source)
        self.assertIn('REQUIRE_API_AUTH must remain 1', source)
        self.assertIn('MIN_MEMORY_GB must not be lower than 24', source)
        with tempfile.TemporaryDirectory(prefix='gemmam5-secure-config-') as temporary:
            checkout = Path(temporary) / 'repo'
            (checkout / 'scripts/lib').mkdir(parents=True)
            (checkout / 'config').mkdir(parents=True)
            shutil.copy2(common, checkout / 'scripts/lib/common.sh')
            shutil.copy2(ROOT / 'config/defaults.conf', checkout / 'config/defaults.conf')
            shutil.copy2(ROOT / 'VERSION', checkout / 'VERSION')
            command = ['bash', '-c', 'source scripts/lib/common.sh; require_secure_target_profile_config']
            accepted = subprocess.run(command, cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            for override, expected in ((
                'REQUIRE_API_AUTH=0\n', 'REQUIRE_API_AUTH must remain 1'),
                ('MIN_MEMORY_GB=1\n', 'MIN_MEMORY_GB must not be lower than 24'),
                ('TARGET_MODEL_NAME=MacBook Pro\n', 'TARGET_MODEL_NAME must remain MacBook Air'),
                ('MIN_MACOS_VERSION=25.0\n', 'MIN_MACOS_VERSION must not be lower than 26.0'),
                ('TARGET_MODEL_IDENTIFIERS=Mac17,1\n', 'TARGET_MODEL_IDENTIFIERS must remain Mac17,3,Mac17,4'),
            ):
                (checkout / 'config/local.conf').write_text(override, encoding='utf-8')
                rejected = subprocess.run(command, cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertNotEqual(0, rejected.returncode, override)
                self.assertIn(expected, rejected.stderr)
            invalid_cases = (
                ('UNKNOWN_SETTING=1\n', 'unsupported configuration key'),
                ('SERVER_PORT=1234\nSERVER_PORT=1235\n', 'duplicate configuration key'),
                (' SERVER_PORT=1234\n', 'non-canonical KEY=VALUE'),
                ('SERVER_PORT=1234\r\n', 'LF line endings'),
            )
            for payload, expected in invalid_cases:
                local = checkout / 'config/local.conf'
                local.write_bytes(payload.encode('utf-8'))
                local.chmod(0o600)
                rejected = subprocess.run(command, cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertNotEqual(0, rejected.returncode, payload)
                self.assertIn(expected, rejected.stderr)
            local = checkout / 'config/local.conf'
            local.write_text('SERVER_PORT=1234\n', encoding='utf-8')
            local.chmod(0o666)
            rejected = subprocess.run(command, cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('group/world-writable', rejected.stderr)

    def test_release_version_reader_rejects_embedded_whitespace(self):
        common = ROOT / 'scripts/lib/common.sh'
        source = common.read_text(encoding='utf-8')
        self.assertNotIn("tr -d '[:space:]'", source)
        with tempfile.TemporaryDirectory(prefix='gemmam5-version-reader-') as temporary:
            checkout = Path(temporary) / 'repo'
            (checkout / 'scripts/lib').mkdir(parents=True)
            shutil.copy2(common, checkout / 'scripts/lib/common.sh')
            (checkout / 'VERSION').write_text('1.1.45\n', encoding='utf-8')
            command = ['bash', '-c', 'source scripts/lib/common.sh; read_release_version']
            accepted = subprocess.run(command, cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual('1.1.45', accepted.stdout)
            for malformed in ('1.1. 45\n', ' 1.1.45\n', '1.1.45 extra\n', '01.1.45\n'):
                (checkout / 'VERSION').write_text(malformed, encoding='utf-8')
                rejected = subprocess.run(command, cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertNotEqual(0, rejected.returncode, malformed)

    def test_single_prediction_profile_is_enforced(self):
        defaults = (ROOT / 'config/defaults.conf').read_text(encoding='utf-8')
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        preflight = (ROOT / 'scripts/preflight.sh').read_text(encoding='utf-8')
        loader = (ROOT / 'scripts/load_model.sh').read_text(encoding='utf-8')
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('MAX_CONCURRENT_PREDICTIONS=1', defaults)
        self.assertIn('MIN_LM_STUDIO_VERSION=0.4.11', defaults)
        self.assertIn('RECOMMENDED_LM_STUDIO_VERSION=0.4.20', defaults)
        self.assertIn('lms_supports_parallel_flag', common)
        self.assertIn('require_lms_parallel_support', common)
        self.assertIn('verify_lms_cli_contract.sh', preflight)
        self.assertIn('check_lm_studio_version.sh', preflight)
        self.assertIn('require_lms_parallel_support', loader)
        self.assertIn('MAX_CONCURRENT_PREDICTIONS must remain 1', loader)
        self.assertIn('--parallel "$parallel"', loader)
        self.assertIn('LM%20Studio-0.4.20%20recommended', readme)
        self.assertIn('enforced by `lms load --parallel 1`', readme)

    def test_unload_requires_explicit_flag_and_confirmation(self):
        text = (ROOT / 'scripts/load_model.sh').read_text(encoding='utf-8')
        self.assertIn('--unload-others', text)
        self.assertIn('confirm_exact "UNLOAD"', text)
        self.assertIn('lms unload --all', text)

    def test_release_package_has_no_transient_state(self):
        inventory = (ROOT / 'REPOSITORY_TREE.txt').read_text(encoding='utf-8')
        manifest = (ROOT / 'SHA256SUMS').read_text(encoding='utf-8')
        self.assertNotIn('.git/', inventory + manifest)
        self.assertNotIn('config/local.conf', inventory + manifest)
        self.assertNotIn('__pycache__', inventory + manifest)
        self.assertEqual([], [p for p in ROOT.rglob('*') if p.is_symlink() and '.git' not in p.parts])

    def test_executable_entrypoints(self):
        paths = list((ROOT / 'scripts').glob('*.sh')) + list((ROOT / 'scripts').glob('*.py'))
        paths += list((ROOT / 'examples').glob('*.sh')) + list((ROOT / 'examples').glob('*.py'))
        for path in paths:
            self.assertTrue(os.access(path, os.X_OK), path)

    def test_no_live_credential_patterns(self):
        patterns = (
            re.compile(r'ghp_[A-Za-z0-9]{30,}'),
            re.compile(r'github_pat_[A-Za-z0-9_]{40,}'),
            re.compile(r'sk-[A-Za-z0-9]{32,}'),
        )
        offenders = []
        for path in ROOT.rglob('*'):
            if not path.is_file() or path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            if any(pattern.search(text) for pattern in patterns):
                offenders.append(path)
        self.assertEqual([], offenders)

    def test_no_private_key_blocks_are_bundled(self):
        markers = ('-----BEGIN ' + 'OPENSSH PRIVATE KEY-----', '-----BEGIN ' + 'PRIVATE KEY-----')
        offenders = []
        for path in ROOT.rglob('*'):
            if not path.is_file() or path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            if any(marker in text for marker in markers):
                offenders.append(path)
        self.assertEqual([], offenders)

    def test_vision_examples_put_image_before_text(self):
        for relative in ('examples/vision_request.py', 'tests/api_smoke_test.py'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertLess(text.index("'type': 'image_url'"), text.index("'type': 'text'"), relative)

    def test_vision_fixture_paths_are_repository_relative(self):
        self.assertIn("Path(__file__).resolve()", (ROOT / 'examples/vision_request.py').read_text(encoding='utf-8'))
        self.assertIn("Path(__file__).resolve()", (ROOT / 'tests/api_smoke_test.py').read_text(encoding='utf-8'))

    def test_tool_result_final_call_does_not_reoffer_tools(self):
        text = (ROOT / 'examples/safe_tool_call.py').read_text(encoding='utf-8')
        self.assertIn("final = api_call(base_url, {'model': args.model, 'messages': messages})", text)

    def test_russian_core_docs_are_localized(self):
        for relative in ('docs/ru/ARCHITECTURE.md', 'docs/ru/TROUBLESHOOTING.md', 'docs/ru/MCP_SAFE_PATTERNS.md'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            cyrillic = sum('А' <= ch <= 'я' or ch in 'Ёё' for ch in text)
            latin = sum('A' <= ch <= 'z' for ch in text)
            self.assertGreater(cyrillic, latin, relative)

    def test_version_metadata_consistent(self):
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        cff = (ROOT / 'CITATION.cff').read_text(encoding='utf-8')
        changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
        self.assertIn(f'version: {version}', cff)
        self.assertRegex(version, r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')
        self.assertEqual(1, changelog.count(f'## {version} '))
        self.assertIn('## 1.1.7 ', changelog)
        expected_directory = f'GemmaM5-1-FullStack-{version}'
        for relative in ('docs/INSTALL_GITHUB_SSH.md', 'docs/ru/INSTALL_GITHUB_SSH.md'):
            publication_guide = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn(f'unzip ~/Downloads/{expected_directory}.zip', publication_guide)
            self.assertIn(f'cd {expected_directory}', publication_guide)
            self.assertIn(f'Release GemmaM5-1 FullStack {version}', publication_guide)
        for relative in (
            'README.md',
            'docs/SCREENSHOTS.md',
            'docs/ru/SCREENSHOTS.md',
            'docs/RELEASE.md',
            'docs/ru/RELEASE.md',
        ):
            current_doc = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn(version, current_doc, relative)

    @staticmethod
    def _markdown_anchors(text: str) -> set[str]:
        anchors: set[str] = set(re.findall(r'<a\s+(?:[^>]*?\s+)?id=["\']([^"\']+)["\']', text, re.I))
        counts: dict[str, int] = {}
        for line in text.splitlines():
            match = re.match(r'^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)
            if not match:
                continue
            heading = match.group(1)
            heading = re.sub(r'!?(?:\[([^]]*)\]\([^)]+\))', r'\1', heading)
            heading = re.sub(r'<[^>]+>', '', heading)
            heading = re.sub(r'[`*_~]', '', heading).strip().lower()
            slug = ''.join(ch for ch in heading if ch.isalnum() or ch in ' -_')
            slug = re.sub(r'\s+', '-', slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
            index = counts.get(slug, 0)
            counts[slug] = index + 1
            anchors.add(slug if index == 0 else f'{slug}-{index}')
        return anchors

    def test_local_markdown_links_and_fragments_resolve(self):
        pattern = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
        missing = []
        for path in ROOT.rglob('*.md'):
            text = path.read_text(encoding='utf-8')
            for match in pattern.finditer(text):
                raw = match.group(1).strip()
                if not raw or '://' in raw or raw.startswith('mailto:'):
                    continue
                file_part, separator, fragment = raw.partition('#')
                target_path = path if not file_part else (path.parent / unquote(file_part)).resolve()
                if not target_path.exists():
                    missing.append((str(path.relative_to(ROOT)), raw, 'missing file'))
                    continue
                if separator and fragment and target_path.suffix.lower() == '.md':
                    anchors = self._markdown_anchors(target_path.read_text(encoding='utf-8'))
                    wanted = unquote(fragment).lower()
                    if wanted not in anchors:
                        missing.append((str(path.relative_to(ROOT)), raw, 'missing fragment'))
        self.assertEqual([], missing)

    def test_release_builder_and_local_artifacts_are_hardened(self):
        builder = (ROOT / 'scripts/build_release.sh').read_text(encoding='utf-8')
        self.assertIn('scripts/validate_manifest.py', builder)
        self.assertIn('--require-files --print-paths > "$manifest_paths"', builder)
        self.assertIn('done < "$manifest_paths"', builder)
        self.assertIn('create_release_zip.py', builder)
        self.assertIn('validate_release_zip.py', builder)
        self.assertIn('validate_checksum_sidecar.py', builder)
        self.assertIn('--expected-root "$package_name"', builder)
        self.assertIn('--repository-root "$PROJECT_ROOT"', builder)
        self.assertIn('cmp -s "$archive" "$second_archive"', builder)
        self.assertIn('unzip -t "$archive"', builder)
        self.assertIn('./scripts/verify_repo.sh', builder)
        self.assertIn('shasum -a 256', builder)
        self.assertIn('scripts/validate_manifest.py', builder)
        validator = (ROOT / 'scripts/validate_manifest.py').read_text(encoding='utf-8')
        self.assertIn('non-canonical release-manifest path', validator)
        self.assertIn('duplicate release-manifest path', validator)
        zip_helper = (ROOT / 'scripts/create_release_zip.py').read_text(encoding='utf-8')
        self.assertIn('FIXED_ZIP_TIME', zip_helper)
        self.assertIn('sorted(package_roots[0].rglob("*")', zip_helper)
        self.assertIn('info.external_attr', zip_helper)
        gitignore = (ROOT / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('artifacts/', gitignore)
        self.assertIn('dist/', gitignore)
        collector = (ROOT / 'scripts/collect_environment.sh').read_text(encoding='utf-8')
        self.assertIn('lms ps --json', collector)
        self.assertIn('summarize_lms_models.py', collector)

    def test_operational_version_reference_validator_rejects_stale_release(self):
        validator = ROOT / 'scripts/verify_version_references.py'
        accepted = subprocess.run([str(validator)], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        with tempfile.TemporaryDirectory(prefix='gemmam5-version-test-') as temporary:
            copied = Path(temporary) / 'repo'
            required = ['VERSION', 'README.md', 'CITATION.cff', 'CHANGELOG.md', 'benchmarks/m5-air-24gb.template.json',
                        'docs/RELEASE.md', 'docs/INSTALL_MODEL.md', 'docs/SCREENSHOTS.md', 'docs/INSTALL_GITHUB_SSH.md',
                        'docs/ru/RELEASE.md', 'docs/ru/INSTALL_MODEL.md', 'docs/ru/SCREENSHOTS.md', 'docs/ru/INSTALL_GITHUB_SSH.md']
            for relative in required:
                source = ROOT / relative
                destination = copied / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            readme = copied / 'README.md'
            version = (copied / 'VERSION').read_text(encoding='utf-8').strip()
            readme.write_text(readme.read_text(encoding='utf-8').replace(version, '1.1.12', 1), encoding='utf-8')
            rejected = subprocess.run([str(validator), '--root', str(copied)], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('stale release references', rejected.stderr)

    def test_benchmark_schema_rejects_fabricated_or_incomplete_measurements(self):
        validator = ROOT / 'scripts/validate_benchmark.py'
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        template = ROOT / 'benchmarks/m5-air-24gb.template.json'
        accepted = subprocess.run([str(validator), str(template), '--expected-repository-version', version], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        data = json.loads(template.read_text(encoding='utf-8'))
        data['status'] = 'measured'
        data['date_utc'] = '2026-07-24T00:00:00Z'
        data['protocol'] = {
            'profile_id': 'fixed-8k-v1', 'run_count': 3,
            'prompt_sha256': '0' * 64, 'cold_start': True,
        }
        with tempfile.TemporaryDirectory(prefix='gemmam5-benchmark-test-') as temporary:
            path = Path(temporary) / 'invalid.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            rejected = subprocess.run([str(validator), str(path), '--expected-repository-version', version], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('software.macos', rejected.stderr)

    def test_canonical_benchmark_and_screenshot_claims_require_owner_evidence(self):
        benchmark = (ROOT / 'benchmarks/README.md').read_text(encoding='utf-8').lower()
        screenshots = (ROOT / 'docs/SCREENSHOTS.md').read_text(encoding='utf-8').lower()
        self.assertIn('only by the repository owner', benchmark)
        self.assertIn('generated or reconstructed', screenshots)


    def test_publication_stages_manifest_only(self):
        publish = (ROOT / 'scripts/publish_repository.sh').read_text(encoding='utf-8')
        stage = (ROOT / 'scripts/stage_release_files.sh').read_text(encoding='utf-8')
        self.assertIn('scripts/stage_release_files.sh', publish)
        self.assertNotIn('git add .', publish)
        self.assertIn('git ls-files --others --exclude-standard', stage)
        self.assertIn('scripts/validate_manifest.py', stage)
        self.assertIn('--require-files --print-paths', stage)
        self.assertIn('git diff --cached --check', stage)
        self.assertIn('Staged only files declared by SHA256SUMS', stage)
        for relative in ('docs/INSTALL_GITHUB_SSH.md', 'docs/ru/INSTALL_GITHUB_SSH.md'):
            guide = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('./scripts/stage_release_files.sh', guide)
            self.assertIn('./scripts/verify_git_inventory.sh --require-clean', guide)
            self.assertNotIn('git add .', guide)
            self.assertNotIn('git config --global', guide)

    def test_ci_pins_current_official_action_releases(self):
        workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn(
            'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1',
            workflow,
        )
        self.assertIn(
            'actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0',
            workflow,
        )
        self.assertNotRegex(workflow, r'actions/(?:checkout|setup-python)@v\\d+')
        self.assertIn('persist-credentials: false', workflow)
        self.assertIn('timeout-minutes: 30', workflow)
        self.assertIn('./scripts/verify_git_inventory.sh --require-clean', workflow)

    def test_environment_reports_use_ignored_artifacts_directory(self):
        for relative in ('README.md', 'docs/INSTALL_MODEL.md', 'docs/ru/INSTALL_MODEL.md'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('artifacts/hardware-environment.txt', text, relative)
            self.assertNotIn('> hardware-environment.txt', text, relative)
        gitignore = (ROOT / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('artifacts/', gitignore)

    def test_checksum_sidecar_validator_is_exact_and_functional(self):
        validator = ROOT / 'scripts/validate_checksum_sidecar.py'
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            archive = directory / 'release.zip'
            archive.write_bytes(b'release-bytes')
            import hashlib
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            sidecar = directory / 'release.zip.sha256'
            sidecar.write_text(f'{digest}  release.zip\n', encoding='ascii')
            accepted = subprocess.run([sys.executable, str(validator), str(sidecar), str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            sidecar.write_text(f'{digest}  another.zip\n', encoding='ascii')
            rejected = subprocess.run([sys.executable, str(validator), str(sidecar), str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('expected', rejected.stderr)

    def test_release_zip_validator_rejects_traversal_and_wrong_root(self):
        validator = ROOT / 'scripts/validate_release_zip.py'
        source = validator.read_text(encoding='utf-8')
        self.assertIn('unsafe or non-file ZIP member', source)
        self.assertIn('duplicate ZIP member names', source)
        self.assertIn('ZIP_STORED', source)
        self.assertIn('FIXED_ZIP_TIME', source)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest = directory / 'SHA256SUMS'
            manifest.write_text('0' * 64 + '  README.md\n', encoding='utf-8')
            archive = directory / 'bad.zip'
            import zipfile
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('../README.md', b'x')
            completed = subprocess.run(
                [sys.executable, str(validator), str(archive), '--expected-root', 'GemmaM5-1-FullStack-1.1.51', '--manifest', str(manifest)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertRegex(completed.stderr.lower(), r'unsafe|non-canonical')

            stage = directory / 'stage'
            package = stage / 'GemmaM5-1-FullStack-1.1.240'
            package.mkdir(parents=True)
            readme = package / 'README.md'
            readme.write_text('ok\n', encoding='utf-8')
            import hashlib
            digest = hashlib.sha256(readme.read_bytes()).hexdigest()
            good_manifest = package / 'SHA256SUMS'
            good_manifest.write_text(f'{digest}  README.md\n', encoding='utf-8')
            good_archive = directory / 'good.zip'
            created = subprocess.run([sys.executable, str(ROOT / 'scripts/create_release_zip.py'), str(stage), str(good_archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            self.assertEqual(0, created.returncode, created.stderr)
            accepted = subprocess.run([sys.executable, str(validator), str(good_archive), '--expected-root', package.name, '--manifest', str(good_manifest), '--repository-root', str(package)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            self.assertEqual(0, accepted.returncode, accepted.stderr)

    def test_release_zip_avoids_deflate_version_variance(self):
        helper = (ROOT / 'scripts/create_release_zip.py').read_text(encoding='utf-8')
        self.assertIn('zipfile.ZIP_STORED', helper)
        self.assertNotIn('zipfile.ZIP_DEFLATED', helper)
        self.assertNotIn('compresslevel=', helper)


    def test_git_inventory_functionally_rejects_extra_tracked_paths(self):
        with tempfile.TemporaryDirectory(prefix='gemmam5-inventory-test-') as temporary:
            checkout = Path(temporary) / 'checkout'
            shutil.copytree(
                ROOT,
                checkout,
                ignore=shutil.ignore_patterns('.git', 'dist', 'artifacts', '__pycache__'),
            )
            commands = (
                ['git', 'init', '-b', 'main'],
                ['git', 'config', 'user.name', 'Repository Test'],
                ['git', 'config', 'user.email', 'repository-test@example.invalid'],
                ['./scripts/stage_release_files.sh'],
                ['git', 'commit', '-m', 'Manifest exact test commit'],
                ['./scripts/verify_git_inventory.sh', '--require-clean'],
            )
            for command in commands:
                subprocess.run(command, cwd=checkout, check=True, text=True, capture_output=True)

            extra = checkout / 'unexpected-tracked.txt'
            extra.write_text('must be rejected\n', encoding='utf-8')
            subprocess.run(['git', 'add', '--', extra.name], cwd=checkout, check=True)
            subprocess.run(
                ['git', 'commit', '-m', 'Add an intentionally forbidden tracked path'],
                cwd=checkout,
                check=True,
                text=True,
                capture_output=True,
            )
            rejected = subprocess.run(
                ['./scripts/verify_git_inventory.sh', '--require-clean'],
                cwd=checkout,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('tracked paths outside the release manifest', rejected.stderr)
            self.assertIn(extra.name, rejected.stderr)

    def test_manifest_path_traversal_is_rejected_functionally(self):
        with tempfile.TemporaryDirectory(prefix='gemmam5-manifest-path-test-') as temporary:
            checkout = Path(temporary) / 'checkout'
            shutil.copytree(
                ROOT,
                checkout,
                ignore=shutil.ignore_patterns('.git', 'dist', 'artifacts', '__pycache__'),
            )
            outside = Path(temporary) / 'outside-secret.txt'
            outside.write_text('must never enter a release archive\n', encoding='utf-8')
            digest = subprocess.run(
                ['shasum', '-a', '256', str(outside)],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.split()[0]
            manifest = checkout / 'SHA256SUMS'
            manifest.write_text(
                manifest.read_text(encoding='utf-8') + f'{digest}  ../{outside.name}\n',
                encoding='utf-8',
            )
            subprocess.run(['git', 'init', '-b', 'main'], cwd=checkout, check=True, capture_output=True)
            rejected = subprocess.run(
                ['./scripts/stage_release_files.sh'],
                cwd=checkout,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('release-manifest path', rejected.stderr)

    def test_model_download_is_exact_by_default_and_fallback_is_explicit(self):
        script = (ROOT / 'scripts/download_model.sh').read_text(encoding='utf-8')
        self.assertIn('interactive_fallback=0', script)
        self.assertIn('--interactive-fallback', script)
        self.assertIn('lms get "$exact_ref" --gguf --yes', script)
        self.assertIn('lms_get_selection_flag', script)
        self.assertIn('lms get "$catalog_id" --gguf "$selection_flag"', script)
        exact_position = script.index('lms get "$exact_ref" --gguf --yes')
        fallback_position = script.index('lms get "$catalog_id" --gguf "$selection_flag"')
        self.assertLess(exact_position, fallback_position)
        self.assertIn('Use --interactive-fallback only for a deliberate manual selection', script)

    def test_release_creation_requires_existing_remote_tag(self):
        for relative in ('docs/RELEASE.md', 'docs/ru/RELEASE.md'):
            release = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('gh release create', release, relative)
            self.assertIn('--verify-tag', release, relative)

    def test_makefile_exposes_standard_gates(self):
        makefile = (ROOT / 'Makefile').read_text(encoding='utf-8')
        self.assertIn('test:\n\t./scripts/run_repository_test_shards.sh', makefile)
        self.assertIn('cli-check:', makefile)
        self.assertIn('review-matrix:', makefile)
        self.assertIn('generate_iteration_matrix.py --verify', makefile)
        self.assertIn('./scripts/verify_lms_cli_contract.sh', makefile)
        self.assertIn('version-check:', makefile)
        self.assertIn('inventory:', makefile)
        self.assertIn('./scripts/verify_git_inventory.sh --require-clean', makefile)
        self.assertIn('provenance:', makefile)
        self.assertIn('./scripts/capture_model_provenance.sh', makefile)

    def test_readme_has_public_engineering_navigation_and_boundaries(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for heading in ('## Try it safely', '## What this repository is — and is not', '## At a glance', '## Repository map', '## Relationship to TurboFieldfare'):
            self.assertIn(heading, readme)
        self.assertIn('Performance remains `not_measured`', readme)
        self.assertIn('silently publishes to GitHub', readme)
        ru = (ROOT / 'docs/ru/README.md').read_text(encoding='utf-8')
        self.assertIn(f'**Текущий релиз:** `{VERSION}`', ru)
        self.assertIn('./scripts/verify_repo.sh', ru)

    def test_positioning_states_external_model_boundary(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        publish = (ROOT / 'scripts/publish_repository.sh').read_text(encoding='utf-8')
        provenance = (ROOT / 'docs/MODEL_PROVENANCE.md').read_text(encoding='utf-8')
        self.assertIn('Repeatable and auditable', readme)
        self.assertNotIn('Reproducible Gemma 4 26B A4B QAT deployment', readme)
        self.assertIn('Repeatable and auditable local Gemma', publish)
        self.assertIn('No model weights included.', publish)
        self.assertIn('not a cryptographic checksum', provenance)
        for relative in ('README.md', 'docs/INSTALL_GITHUB_SSH.md', 'docs/ru/INSTALL_GITHUB_SSH.md'):
            guide = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('chmod +x scripts/*.sh scripts/*.py examples/*.sh examples/*.py', guide)

    def test_model_provenance_writer_filters_paths_and_requires_exact_profile(self):
        writer = ROOT / 'scripts/write_model_provenance.py'
        with tempfile.TemporaryDirectory(prefix='gemmam5-provenance-test-') as temporary:
            directory = Path(temporary)
            inventory = directory / 'inventory.json'
            output = directory / 'provenance.json'
            model_path = 'google/gemma-4-26b-a4b-qat/gemma-4-26b-a4b-qat-Q4_0.gguf'
            model_key = 'google/gemma-4-26b-a4b-qat@q4_0'
            inventory.write_text(json.dumps({'models': [{
                'modelKey': model_key,
                'displayName': 'Gemma 4 26B A4B QAT Q4_0',
                'format': 'gguf',
                'quantization': {'name': 'Q4_0', 'path': '/private/model'},
                'path': model_path,
                'deviceIdentifier': None,
                'sizeBytes': 15600000000,
            }]}), encoding='utf-8')
            accepted = subprocess.run([
                str(writer), '--inventory', str(inventory), '--output', str(output),
                '--repository-version', (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
                '--catalog-id', 'google/gemma-4-26b-a4b-qat',
                '--required-quantization', 'q4_0',
                '--resolved-model-key', model_key,
                '--resolved-model-path', model_path,
                '--collected-utc', '2026-07-24T00:00:00Z',
            ], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            record = json.loads(output.read_text(encoding='utf-8'))
            encoded = json.dumps(record)
            self.assertNotIn('/Users/private', encoded)
            self.assertNotIn('/private/model', encoded)
            self.assertNotIn(model_path, encoded)
            self.assertEqual('q4_0', record['required_quantization'])
            self.assertEqual(64, len(record['resolved_model_path_sha256']))
            self.assertFalse(record['privacy']['local_paths_included'])

            rejected = subprocess.run([
                str(writer), '--inventory', str(inventory), '--output', str(output),
                '--repository-version', (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
                '--catalog-id', 'google/gemma-4-26b-a4b-qat',
                '--required-quantization', 'q4_0',
                '--resolved-model-key', 'google/gemma-4-26b-a4b-qat@q8_0',
                '--resolved-model-path', model_path,
            ], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('does not prove the exact', rejected.stderr)

    def test_manifest_validator_rejects_dot_components_and_duplicates(self):
        validator = ROOT / 'scripts/validate_manifest.py'
        with tempfile.TemporaryDirectory(prefix='gemmam5-manifest-canonical-test-') as temporary:
            checkout = Path(temporary)
            target = checkout / 'docs' / 'file.md'
            target.parent.mkdir(parents=True)
            target.write_text('x\n', encoding='utf-8')
            digest = '0' * 64
            for lines, expected in (
                ([f'{digest}  docs/./file.md'], 'non-canonical release-manifest path'),
                ([f'{digest}  docs/file.md', f'{digest}  docs/file.md'], 'duplicate release-manifest path'),
            ):
                manifest = checkout / 'SHA256SUMS'
                manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')
                result = subprocess.run(
                    [str(validator), str(manifest), '--root', str(checkout), '--require-files'],
                    check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn(expected, result.stderr)

    def test_model_discovery_rejects_non_q4_quantization(self):
        module_path = ROOT / 'scripts/resolve_model_identity.py'
        spec = importlib.util.spec_from_file_location('resolve_model_identity_test', module_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        q8_only = {'models': [{
            'modelKey': 'google/gemma-4-26b-a4b-qat@q8_0',
            'path': 'google/gemma-4-26b-a4b-qat/model-Q8_0.gguf',
            'displayName': 'Gemma 4 26B A4B QAT Q8_0',
            'format': 'gguf',
            'deviceIdentifier': None,
        }]}
        exact_q4 = {'models': [{
            'modelKey': 'google/gemma-4-26b-a4b-qat@q4_0',
            'path': 'google/gemma-4-26b-a4b-qat/model-Q4_0.gguf',
            'displayName': 'Gemma 4 26B A4B QAT Q4_0',
            'format': 'gguf',
            'deviceIdentifier': None,
        }]}
        self.assertEqual([], module.choose_identities(q8_only))
        identities = module.choose_identities(exact_q4)
        self.assertEqual(1, len(identities))
        self.assertEqual('google/gemma-4-26b-a4b-qat/model-Q4_0.gguf', identities[0].path)
        self.assertEqual('google/gemma-4-26b-a4b-qat@q4_0', identities[0].model_key)

    def test_model_discovery_rejects_lookalike_catalog_identity(self):
        module_path = ROOT / 'scripts/resolve_model_identity.py'
        spec = importlib.util.spec_from_file_location('resolve_model_identity_catalog_test', module_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        lookalike = {'models': [{
            'modelKey': 'third-party/gemma-4-26b-a4b-qat@q4_0',
            'path': 'third-party/gemma-4-26b-a4b-qat/model-Q4_0.gguf',
            'displayName': 'Gemma 4 26B A4B QAT Q4_0',
            'format': 'gguf',
            'deviceIdentifier': None,
        }]}
        self.assertEqual([], module.choose_identities(lookalike))
        with self.assertRaises(SystemExit):
            module.resolve(lookalike)

    def test_listener_verification_is_mandatory_and_retried(self):
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        self.assertIn('require_command lsof', common)
        self.assertIn('sleep 1', common)
        self.assertIn('after $attempts checks', common)
        self.assertNotIn('lsof is unavailable; listener address could not be independently verified', common)


    def test_listener_verification_functionally_retries_and_rejects_wildcard(self):
        with tempfile.TemporaryDirectory(prefix='gemmam5-listener-test-') as temporary:
            bindir = Path(temporary) / 'bin'
            bindir.mkdir()
            counter = Path(temporary) / 'counter'
            fake_lsof = bindir / 'lsof'
            fake_lsof.write_text(
                '#!/usr/bin/env bash\n'
                'count=0; [ ! -f "$LISTENER_COUNTER" ] || count=$(cat "$LISTENER_COUNTER")\n'
                'count=$((count + 1)); printf "%s" "$count" > "$LISTENER_COUNTER"\n'
                'if [ "$count" -lt 3 ]; then exit 1; fi\n'
                'printf "n127.0.0.1:1234\\n"\n',
                encoding='utf-8',
            )
            fake_lsof.chmod(0o755)
            environment = os.environ.copy()
            environment['PATH'] = f'{bindir}:{environment["PATH"]}'
            environment['LISTENER_COUNTER'] = str(counter)
            command = 'source scripts/lib/common.sh; assert_loopback_listener 1234 4'
            accepted = subprocess.run(
                ['bash', '-c', command], cwd=ROOT, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
            )
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual('3', counter.read_text(encoding='utf-8'))

            fake_lsof.write_text(
                '#!/usr/bin/env bash\nprintf "n*:1234\\n"\n',
                encoding='utf-8',
            )
            fake_lsof.chmod(0o755)
            rejected = subprocess.run(
                ['bash', '-c', command], cwd=ROOT, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('listener address is not a numeric IP address', rejected.stderr)

            fake_lsof.write_text(
                '#!/usr/bin/env bash\n'
                'printf "n127.0.0.1:1234\\n"\n'
                'printf "n192.168.1.77:1234\\n"\n',
                encoding='utf-8',
            )
            fake_lsof.chmod(0o755)
            mixed = subprocess.run(
                ['bash', '-c', command], cwd=ROOT, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, mixed.returncode)
            self.assertIn('non-loopback listener detected', mixed.stderr)

    def test_server_status_requires_running_expected_port(self):
        environment = os.environ.copy()
        command = (
            "lms() { printf '%s\n' \"$LMS_STATUS_JSON\"; }; "
            "source scripts/lib/common.sh; assert_lms_server_status 1234"
        )

        environment['LMS_STATUS_JSON'] = '{"running":true,"port":1234}'
        accepted = subprocess.run(
            ['bash', '-c', command], cwd=ROOT, env=environment, check=False,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        self.assertIn('running=true on port 1234', accepted.stdout)

        for payload in ('{"running":false,"port":1234}', '{"running":true,"port":4321}', 'not-json'):
            environment['LMS_STATUS_JSON'] = payload
            rejected = subprocess.run(
                ['bash', '-c', command], cwd=ROOT, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
            )
            self.assertNotEqual(0, rejected.returncode, payload)

    def test_remote_creation_and_origin_handling_fail_closed(self):
        publish = (ROOT / 'scripts/publish_repository.sh').read_text(encoding='utf-8')
        self.assertIn('gh repo create "$repo_full_name"', publish)
        self.assertIn('--expected-default-branch main', publish)
        self.assertNotIn('--source .', publish)
        self.assertNotIn('--remote origin', publish)
        self.assertNotIn('git remote set-url origin "$remote_url"', publish)
        self.assertIn('Refusing to rewrite it implicitly', publish)
        self.assertIn('git remote add origin "$remote_url"', publish)

        with tempfile.TemporaryDirectory(prefix='gemmam5-origin-guard-test-') as temporary:
            checkout = Path(temporary) / 'checkout'
            shutil.copytree(
                ROOT, checkout,
                ignore=shutil.ignore_patterns('.git', 'dist', 'artifacts', '__pycache__'),
            )
            bindir = Path(temporary) / 'bin'
            bindir.mkdir()
            fake_ssh = bindir / 'ssh'
            fake_ssh.write_text(
                '#!/usr/bin/env bash\n'
                'if [ "${1:-}" = -G ]; then\n'
                '  printf "hostname github.com\\nuser git\\nidentitiesonly yes\\nproxycommand none\\nproxyjump none\\nidentityfile %s/.ssh/id_ed25519_github_gendalf71_m5\\n" "$HOME"\n'
                '  exit 0\n'
                'fi\n'
                'printf "Hi Gendalf71! You have successfully authenticated, but GitHub does not provide shell access.\\n" >&2\n'
                'exit 1\n',
                encoding='utf-8',
            )
            fake_ssh.chmod(0o755)
            fake_gh = bindir / 'gh'
            fake_gh.write_text(
                '#!/usr/bin/env bash\n'
                'if [ "${1:-}" = api ]; then printf "Gendalf71\n"; exit 0; fi\n'
                'exit 0\n',
                encoding='utf-8',
            )
            fake_gh.chmod(0o755)
            environment = os.environ.copy()
            home = Path(temporary) / 'home'
            (home / '.ssh').mkdir(parents=True)
            (home / '.ssh' / 'id_ed25519_github_gendalf71_m5').write_text('test-key\n', encoding='utf-8')
            environment['HOME'] = str(home)
            environment['PATH'] = f'{bindir}:{environment["PATH"]}'
            subprocess.run(['git', 'init', '-b', 'main'], cwd=checkout, check=True, capture_output=True)
            subprocess.run(['git', 'config', '--local', 'user.name', 'Grigoriy Dedenko'], cwd=checkout, check=True)
            subprocess.run(['git', 'config', '--local', 'user.email', '12345+Gendalf71@users.noreply.github.com'], cwd=checkout, check=True)
            subprocess.run(
                ['git', 'remote', 'add', 'origin', 'git@example.invalid:wrong/repository.git'],
                cwd=checkout, check=True,
            )
            result = subprocess.run(
                ['./scripts/publish_repository.sh', '--execute'],
                cwd=checkout, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn('Refusing to rewrite it implicitly', result.stderr)
            origin = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'], cwd=checkout, check=True,
                text=True, stdout=subprocess.PIPE,
            ).stdout.strip()
            self.assertEqual('git@example.invalid:wrong/repository.git', origin)


    def test_mcp_request_overrides_model_and_validates_allowlist(self):
        with tempfile.TemporaryDirectory(prefix='gemmam5-mcp-request-test-') as temporary:
            bindir = Path(temporary) / 'bin'
            bindir.mkdir()
            fake_curl = bindir / 'curl'
            fake_curl.write_text(
                '#!/usr/bin/env bash\n'
                'previous=""\n'
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--data-binary" ]; then case "$argument" in @*) cat -- "${argument#@}" ;; esac; fi\n'
                '  previous="$argument"\n'
                'done\n',
                encoding='utf-8',
            )
            fake_curl.chmod(0o755)
            environment = os.environ.copy()
            environment['PATH'] = f'{bindir}:{environment["PATH"]}'
            environment['MODEL_IDENTIFIER'] = 'google/gemma-4-26b-a4b-qat@q4_0'
            environment['LM_API_TOKEN'] = 'test-token-not-a-real-secret'
            result = subprocess.run(
                [str(ROOT / 'examples/mcp_request.sh')], cwd=Path(temporary), env=environment,
                check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(environment['MODEL_IDENTIFIER'], payload['model'])
            self.assertEqual(['model_search'], payload['integrations'][0]['allowed_tools'])
            self.assertIn('MCP is disabled by default', result.stderr)
            self.assertIn(f'Target model: {environment["MODEL_IDENTIFIER"]}', result.stderr)
            self.assertIn('Target endpoint: http://127.0.0.1:1234/api/v1', result.stderr)

            remote_environment = environment.copy()
            remote_environment['LM_NATIVE_BASE_URL'] = 'https://203.0.113.1/api/v1'
            remote_environment['LM_API_TOKEN'] = 'test-token-not-a-real-secret'
            remote_rejected = subprocess.run(
                [str(ROOT / 'examples/mcp_request.sh')], cwd=Path(temporary), env=remote_environment,
                check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, remote_rejected.returncode)
            self.assertIn('Refusing to send request data or LM_API_TOKEN', remote_rejected.stderr)

            remote_allowed = subprocess.run(
                [str(ROOT / 'examples/mcp_request.sh'), '--allow-remote-base-url'],
                cwd=Path(temporary), env=remote_environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(0, remote_allowed.returncode, remote_allowed.stderr)
            self.assertIn('may be sent to a remote endpoint', remote_allowed.stderr)

            unsafe = Path(temporary) / 'unsafe.json'
            unsafe.write_text(json.dumps({
                'model': 'ignored',
                'input': 'test',
                'integrations': [{
                    'type': 'ephemeral_mcp',
                    'server_url': 'https://example.invalid/mcp',
                    'allowed_tools': [],
                }],
            }), encoding='utf-8')
            rejected = subprocess.run(
                ['./examples/mcp_request.sh', str(unsafe)], cwd=ROOT, env=environment,
                check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('allowed_tools must be a non-empty list', rejected.stderr)

    def test_target_profile_is_fixed_before_download(self):
        script = (ROOT / 'scripts/download_model.sh').read_text(encoding='utf-8')
        guard = 'require_target_model_profile "$catalog_id" "$quantization"'
        self.assertIn(guard, script)
        self.assertLess(script.index(guard), script.index('lms get "$exact_ref" --gguf'))
        command = (
            'source scripts/lib/common.sh; '
            'require_target_model_profile google/gemma-4-26b-a4b-qat q4_0; '
            'require_target_model_profile google/gemma-4-26b-a4b-qat q8_0'
        )
        result = subprocess.run(
            ['bash', '-c', command], cwd=ROOT, check=False,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn('MODEL_QUANTIZATION must remain q4_0', result.stderr)

    def test_model_key_override_is_verified_against_inventory(self):
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        estimate = (ROOT / 'scripts/estimate_model.sh').read_text(encoding='utf-8')
        load = (ROOT / 'scripts/load_model.sh').read_text(encoding='utf-8')
        self.assertIn('--verify-model-key "$MODEL_KEY"', common)
        self.assertIn('identity="$(resolve_exact_model_identity)"', estimate)
        self.assertIn('identity="$(resolve_exact_model_identity)"', load)
        self.assertNotIn('${MODEL_KEY:-', estimate + load)

        with tempfile.TemporaryDirectory(prefix='gemmam5-model-key-override-test-') as temporary:
            bindir = Path(temporary) / 'bin'
            bindir.mkdir()
            fake_lms = bindir / 'lms'
            fake_lms.write_text(
                '#!/usr/bin/env bash\n'
                'if [ "$1 $2" = "ls --json" ]; then cat "$LMS_JSON"; exit 0; fi\n'
                'exit 0\n',
                encoding='utf-8',
            )
            fake_lms.chmod(0o755)
            model_path = 'google/gemma-4-26b-a4b-qat/model-Q4_0.gguf'
            model_key = 'google/gemma-4-26b-a4b-qat@q4_0'
            exact = Path(temporary) / 'exact.json'
            exact.write_text(json.dumps({'models': [{
                'modelKey': model_key,
                'path': model_path,
                'displayName': 'Gemma 4 26B A4B QAT Q4_0',
                'format': 'gguf',
                'deviceIdentifier': None,
            }]}), encoding='utf-8')
            environment = os.environ.copy()
            environment['PATH'] = f'{bindir}:{environment["PATH"]}'
            environment['MODEL_KEY'] = model_key
            environment['LMS_JSON'] = str(exact)
            accepted = subprocess.run(
                ['bash', '-c', 'source scripts/lib/common.sh; resolve_exact_model_identity'],
                cwd=ROOT, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual(f'{model_path}\t{model_key}', accepted.stdout.strip())

            environment['MODEL_KEY'] = 'google/gemma-4-26b-a4b-qat@q8_0'
            rejected = subprocess.run(
                ['bash', '-c', 'source scripts/lib/common.sh; resolve_exact_model_identity'],
                cwd=ROOT, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn('no unique local Gemma 4', rejected.stderr)

    def test_model_identity_resolver_rejects_ambiguity_and_remote_entries(self):
        module_path = ROOT / 'scripts/resolve_model_identity.py'
        spec = importlib.util.spec_from_file_location('resolve_model_identity_ambiguity_test', module_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        local = {
            'modelKey': 'google/gemma-4-26b-a4b-qat@q4_0',
            'path': 'google/gemma-4-26b-a4b-qat/a-Q4_0.gguf',
            'displayName': 'Gemma 4 26B A4B QAT Q4_0',
            'format': 'gguf',
            'deviceIdentifier': None,
        }
        remote = dict(local, path='remote/model-Q4_0.gguf', deviceIdentifier='remote-mac')
        self.assertEqual(1, len(module.choose_identities({'models': [local, remote]})))
        duplicate = dict(local, path='google/gemma-4-26b-a4b-qat/b-Q4_0.gguf')
        with self.assertRaises(SystemExit):
            module.resolve({'models': [local, duplicate]})

    def test_model_identity_pair_is_machine_readable_and_exact_load_uses_path(self):
        resolver = (ROOT / 'scripts/resolve_model_identity.py').read_text(encoding='utf-8')
        estimate = (ROOT / 'scripts/estimate_model.sh').read_text(encoding='utf-8')
        loader = (ROOT / 'scripts/load_model.sh').read_text(encoding='utf-8')
        downloader = (ROOT / 'scripts/download_model.sh').read_text(encoding='utf-8')
        self.assertIn('["lms", "ls", "--json"]', resolver)
        self.assertNotIn('--variants', resolver)
        self.assertIn('ModelIdentity(path=path, model_key=model_key)', resolver)
        self.assertIn('catalog_id_from_model_key(model_key) == TARGET_CATALOG', resolver)
        for script in (estimate, loader):
            self.assertIn("IFS=$'\\t' read -r model_path model_key", script)
            self.assertIn('lms load "$model_path"', script)
            self.assertNotIn('lms load "$model_key"', script)
            self.assertIn('--exact', script)
        self.assertIn('Verified local model path:', downloader)
        self.assertIn('Verified local modelKey:', downloader)
        self.assertIn('lms unload "$identifier"', loader)
        self.assertIn('trap cleanup_failed_load EXIT', loader)

    def test_git_identity_validator_rejects_placeholders(self):
        validator = ROOT / 'scripts/validate_git_identity.py'
        valid = subprocess.run(
            [sys.executable, str(validator), '--name', 'Grigoriy Dedenko', '--email', '12345+Gendalf71@users.noreply.github.com'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        self.assertEqual(0, valid.returncode, valid.stderr)
        invalid = subprocess.run(
            [sys.executable, str(validator), '--name', 'Grigoriy Dedenko', '--email', 'YOUR_VERIFIED_OR_NOREPLY_GITHUB_EMAIL'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        self.assertNotEqual(0, invalid.returncode)
        self.assertRegex(invalid.stderr.lower(), r'canonical|placeholder')

    def test_publication_requires_repository_local_git_identity(self):
        publish = (ROOT / 'scripts/publish_repository.sh').read_text(encoding='utf-8')
        self.assertIn('git config --local --get user.name', publish)
        self.assertIn('git config --local --get user.email', publish)
        self.assertNotIn('git config user.name || true', publish)
        self.assertNotIn('git config user.email || true', publish)
        self.assertIn('validate_git_identity.py', publish)

        with tempfile.TemporaryDirectory(prefix='gemmam5-local-identity-test-') as temporary:
            temporary_path = Path(temporary)
            checkout = temporary_path / 'checkout'
            shutil.copytree(
                ROOT, checkout,
                ignore=shutil.ignore_patterns('.git', 'dist', 'artifacts', '__pycache__'),
            )
            home = temporary_path / 'home'
            home.mkdir()
            (home / '.ssh').mkdir()
            (home / '.ssh' / 'id_ed25519_github_gendalf71_m5').write_text('test-key\n', encoding='utf-8')
            bindir = temporary_path / 'bin'
            bindir.mkdir()

            fake_ssh = bindir / 'ssh'
            fake_ssh.write_text(
                '#!/usr/bin/env bash\n'
                'if [ "${1:-}" = -G ]; then\n'
                '  printf "hostname github.com\\nuser git\\nidentitiesonly yes\\nproxycommand none\\nproxyjump none\\nidentityfile %s/.ssh/id_ed25519_github_gendalf71_m5\\n" "$HOME"\n'
                '  exit 0\n'
                'fi\n'
                'printf "Hi Gendalf71! You have successfully authenticated, but GitHub does not provide shell access.\\n" >&2\n'
                'exit 1\n',
                encoding='utf-8',
            )
            fake_ssh.chmod(0o755)
            fake_gh = bindir / 'gh'
            fake_gh.write_text(
                '#!/usr/bin/env bash\n'
                'if [ "${1:-}" = api ]; then printf "Gendalf71\\n"; exit 0; fi\n'
                'exit 0\n',
                encoding='utf-8',
            )
            fake_gh.chmod(0o755)

            environment = os.environ.copy()
            environment['HOME'] = str(home)
            environment['PATH'] = f'{bindir}:{environment["PATH"]}'
            subprocess.run(
                ['git', 'config', '--global', 'user.name', 'Inherited Global Name'],
                cwd=checkout, env=environment, check=True,
            )
            subprocess.run(
                ['git', 'config', '--global', 'user.email', 'global@example.invalid'],
                cwd=checkout, env=environment, check=True,
            )
            effective = subprocess.run(
                ['git', 'config', 'user.name'], cwd=checkout, env=environment,
                check=True, text=True, stdout=subprocess.PIPE,
            )
            self.assertEqual('Inherited Global Name', effective.stdout.strip())

            result = subprocess.run(
                ['./scripts/publish_repository.sh', '--execute'],
                cwd=checkout, env=environment, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn('Set repository-local Git identity', result.stderr)

    def test_safe_tool_call_restricts_endpoint_and_argument_shape(self):
        module_path = ROOT / 'examples/safe_tool_call.py'
        spec = importlib.util.spec_from_file_location('safe_tool_call_security_test', module_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        local = 'http://127.0.0.1:1234/v1/'
        self.assertEqual('http://127.0.0.1:1234/v1', module.validate_api_base_url(local))
        self.assertEqual(
            'https://example.invalid/v1',
            module.validate_api_base_url('https://example.invalid/v1', allow_remote=True),
        )
        for unsafe_url in (
            'https://example.invalid/v1',
            'http://127.0.0.1.evil.invalid/v1',
            'http://user:pass@127.0.0.1:1234/v1',
            'http://127.0.0.1:1234/v1?token=secret',
        ):
            with self.assertRaises(ValueError, msg=unsafe_url):
                module.validate_api_base_url(unsafe_url)

        valid = [{
            'id': 'call-1',
            'function': {'name': 'read_memory_pressure', 'arguments': '{}'},
        }]
        call_id, arguments = module.validate_memory_pressure_call(valid)
        self.assertEqual('call-1', call_id)
        self.assertEqual({}, arguments)

        invalid_calls = [
            [],
            valid + valid,
            [{'id': '', 'function': {'name': 'read_memory_pressure', 'arguments': '{}'}}],
            [{'id': 'call-1', 'function': {'name': 'other_tool', 'arguments': '{}'}}],
            [{'id': 'call-1', 'function': {'name': 'read_memory_pressure', 'arguments': []}}],
            [{'id': 'call-1', 'function': {'name': 'read_memory_pressure', 'arguments': '[]'}}],
            [{'id': 'call-1', 'function': {'name': 'read_memory_pressure', 'arguments': 'null'}}],
            [{'id': 'call-1', 'function': {'name': 'read_memory_pressure', 'arguments': 'false'}}],
            [{'id': 'call-1', 'function': {'name': 'read_memory_pressure', 'arguments': '{"x":1}'}}],
        ]
        for calls in invalid_calls:
            with self.assertRaises(ValueError, msg=repr(calls)):
                module.validate_memory_pressure_call(calls)

    def test_gpu_offload_and_exact_load_contract_are_fail_closed(self):
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        estimate = (ROOT / 'scripts/estimate_model.sh').read_text(encoding='utf-8')
        loader = (ROOT / 'scripts/load_model.sh').read_text(encoding='utf-8')
        self.assertIn('require_gpu_offload()', common)
        self.assertNotIn('max|auto|off|0|0.*', estimate + loader)
        for script in (estimate, loader):
            self.assertIn('--exact', script)
            self.assertIn('--local', script)
            self.assertIn('--yes', script)
            self.assertIn('model_path', script)
            self.assertIn('model_key', script)
        self.assertIn('verify_loaded_model.py', loader)
        self.assertIn('--expected-model-path "$model_path"', loader)
        self.assertIn('--expected-model-key "$model_key"', loader)
        with tempfile.TemporaryDirectory(prefix='gemmam5-gpu-') as temporary:
            checkout = Path(temporary) / 'repo'
            (checkout / 'scripts/lib').mkdir(parents=True)
            (checkout / 'config').mkdir(parents=True)
            shutil.copy2(ROOT / 'scripts/lib/common.sh', checkout / 'scripts/lib/common.sh')
            shutil.copy2(ROOT / 'config/defaults.conf', checkout / 'config/defaults.conf')
            shutil.copy2(ROOT / 'VERSION', checkout / 'VERSION')
            command = ['bash', '-c', 'source scripts/lib/common.sh; require_gpu_offload "$1"', 'test']
            for accepted in ('off', 'max', '0', '0.25', '1', '1.0'):
                result = subprocess.run(command + [accepted], cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(0, result.returncode, (accepted, result.stderr))
            for rejected in ('auto', '0.*', '.5', '1.1', '-0.1', 'nan'):
                result = subprocess.run(command + [rejected], cwd=checkout, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertNotEqual(0, result.returncode, rejected)

    def test_loaded_model_postcondition_verifier(self):
        verifier = ROOT / 'scripts/verify_loaded_model.py'
        model_path = 'google/gemma-4-26b-a4b-qat/model-Q4_0.gguf'
        model_key = 'google/gemma-4-26b-a4b-qat@q4_0'
        base = [
            str(verifier),
            '--expected-model-path', model_path,
            '--expected-model-key', model_key,
            '--expected-identifier', 'gemma4-local',
            '--expected-parallel', '1',
        ]
        valid = [{'path': model_path, 'modelKey': model_key, 'identifier': 'gemma4-local', 'parallel': 1}]
        ready = subprocess.run(base + ['--phase', 'pre'], input='[]', text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, ready.returncode, ready.stderr)
        self.assertEqual('ready', ready.stdout.strip())
        already = subprocess.run(base + ['--phase', 'pre'], input=json.dumps(valid), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, already.returncode, already.stderr)
        self.assertEqual('already-loaded', already.stdout.strip())
        accepted = subprocess.run(base + ['--phase', 'post'], input=json.dumps(valid), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        for invalid in (
            [],
            [{'path': 'other', 'modelKey': model_key, 'identifier': 'gemma4-local', 'parallel': 1}],
            [{'path': model_path, 'modelKey': 'other', 'identifier': 'gemma4-local', 'parallel': 1}],
            [{'path': model_path, 'modelKey': model_key, 'identifier': 'gemma4-local', 'parallel': 4}],
            valid + valid,
        ):
            rejected = subprocess.run(base + ['--phase', 'post'], input=json.dumps(invalid), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(0, rejected.returncode, invalid)
        conflict = [{'path': model_path, 'modelKey': model_key, 'identifier': 'other-id', 'parallel': 1}]
        rejected_pre = subprocess.run(base + ['--phase', 'pre'], input=json.dumps(conflict), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, rejected_pre.returncode)
        self.assertIn('conflict', rejected_pre.stderr)

    def test_runtime_compatibility_and_final_audit_are_explicit(self):
        compatibility = (ROOT / 'docs/COMPATIBILITY.md').read_text(encoding='utf-8')
        final_audit = (ROOT / 'docs/FINAL_AUDIT.md').read_text(encoding='utf-8')
        defaults = (ROOT / 'config/defaults.conf').read_text(encoding='utf-8')
        self.assertIn('71bd99ccf882a0410cfd574ee220a99083608930', compatibility)
        self.assertIn('0.4.11', compatibility)
        self.assertIn('0.4.20', compatibility)
        self.assertIn('ModelInfo.path', compatibility)
        self.assertIn('modelKey', compatibility)
        self.assertIn('MIN_LM_STUDIO_VERSION=0.4.11', defaults)
        self.assertIn('RECOMMENDED_LM_STUDIO_VERSION=0.4.20', defaults)
        self.assertIn('Mac17,3', compatibility)
        self.assertIn('Mac17,4', compatibility)
        self.assertIn(f'Repository version: {VERSION}', final_audit)
        self.assertIn('The supplied 1.1.150 archive', final_audit)
        self.assertIn('revision-ledger-1.1.240.json', final_audit)
        self.assertIn('Unresolved critical repository or documentation defects: **0**', final_audit)
        self.assertIn('physical benchmark', final_audit)

    def test_current_ci_release_and_runtime_boundaries(self):
        workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn('timeout-minutes: 30', workflow)
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('cancel-in-progress: true', workflow)
        self.assertIn('fetch-depth: 1', workflow)
        self.assertIn('--source-already-verified', workflow)
        self.assertIn("PYTHONDONTWRITEBYTECODE: '1'", workflow)
        self.assertIn('actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1', workflow)
        self.assertIn('actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0', workflow)
        defaults = (ROOT / 'config/defaults.conf').read_text(encoding='utf-8')
        self.assertIn('RECOMMENDED_LM_STUDIO_VERSION=0.4.20', defaults)
        compatibility = (ROOT / 'docs/COMPATIBILITY.md').read_text(encoding='utf-8')
        self.assertIn('M1/M2/M3/M4, not M5', compatibility)

    def test_release_assurance_is_machine_readable_and_closed(self):
        record = json.loads((ROOT / ASSURANCE_RELATIVE).read_text(encoding='utf-8'))
        self.assertEqual(VERSION, record['repository_version'])
        self.assertEqual(0, record['critical_findings_remaining'])
        self.assertEqual(0, record['major_findings_remaining'])
        self.assertEqual('not_measured', record['hardware_benchmark_status'])
        self.assertEqual('not_captured', record['runtime_screenshot_status'])
        self.assertEqual(2160, record['matrix']['total_control_passes'])
        checked = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_release_assurance.py')], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(0, checked.returncode, checked.stderr)

    def test_canonical_repository_identity_has_no_operational_drift(self):
        canonical = 'Gendalf71/GemmaM5-1-FullStack'
        old = 'Gendalf71/GemmaM5-FullStack'
        operational = (
            'README.md', 'CITATION.cff', 'benchmarks/README.md',
            'docs/INSTALL_GITHUB_SSH.md', 'docs/RELEASE.md',
            'docs/ru/INSTALL_GITHUB_SSH.md', 'docs/ru/RELEASE.md',
        )
        for relative in operational:
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn(canonical, text, relative)
            self.assertNotIn(old, text, relative)
        for relative in ('scripts/publish_repository.sh', 'scripts/create_github_release.sh'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('owner="Gendalf71"', text, relative)
            self.assertIn('repo_name="GemmaM5-1-FullStack"', text, relative)
            self.assertNotIn('repo_name="GemmaM5-FullStack"', text, relative)
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertIn('package_name="GemmaM5-1-FullStack-$version"', (ROOT / 'scripts/build_release.sh').read_text(encoding='utf-8'))

    def test_current_target_documents_share_macos_26_floor(self):
        defaults = (ROOT / 'config/defaults.conf').read_text(encoding='utf-8')
        self.assertIn('MIN_MACOS_VERSION=26.0', defaults)
        current_documents = (
            'README.md', 'docs/COMPATIBILITY.md', 'docs/INSTALL_MODEL.md',
            'docs/SECURITY.md', 'docs/TROUBLESHOOTING.md',
            'docs/ru/COMPATIBILITY.md', 'docs/ru/INSTALL_MODEL.md',
            'docs/ru/SECURITY.md', 'docs/ru/TROUBLESHOOTING.md',
        )
        for relative in current_documents:
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('26.0', text, relative)
            self.assertNotIn('macOS 14.0', text, relative)
            self.assertNotIn('MIN_MACOS_VERSION=14.0', text, relative)

    def test_text_files_have_clean_line_endings(self):
        offenders = []
        binary_suffixes = {'.png', '.jpg', '.jpeg', '.webp'}
        for path in ROOT.rglob('*'):
            if not path.is_file() or path.name == 'SHA256SUMS' or path.suffix.lower() in binary_suffixes:
                continue
            if any(part in {'.git', 'dist', 'artifacts', '__pycache__'} for part in path.parts):
                continue
            try:
                raw = path.read_bytes()
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if b'\r\n' in raw or b'\r' in raw:
                offenders.append((str(path.relative_to(ROOT)), 'non-LF line ending'))
            if not text.endswith('\n'):
                offenders.append((str(path.relative_to(ROOT)), 'missing final newline'))
            if text.endswith('\n\n'):
                offenders.append((str(path.relative_to(ROOT)), 'extra blank line at EOF'))
            for number, line in enumerate(text.splitlines(), 1):
                if line.endswith((' ', '\t')):
                    offenders.append((str(path.relative_to(ROOT)), f'trailing whitespace line {number}'))
        self.assertEqual([], offenders)

    def test_openai_api_clients_share_fail_closed_endpoint_policy(self):
        module_path = ROOT / 'scripts/api_url_policy.py'
        spec = importlib.util.spec_from_file_location('api_url_policy_test', module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertEqual('http://127.0.0.1:1234/v1', module.validate_api_base_url('http://127.0.0.1:1234/v1/'))
        self.assertEqual('http://[::1]:1234/v1', module.validate_api_base_url('http://[::1]:1234/v1'))
        for value in ('https://example.invalid/v1', 'http://localhost:1234/v1', 'http://127.0.0.1:1234/api/v2', 'http://user:pass@127.0.0.1:1234/v1', 'http://127.0.0.1:1234/v1?token=x'):
            with self.assertRaises(ValueError, msg=value):
                module.validate_api_base_url(value)
        self.assertEqual('https://example.invalid/v1', module.validate_api_base_url('https://example.invalid/v1', allow_remote=True))
        with self.assertRaises(ValueError):
            module.validate_api_base_url('http://example.invalid/v1', allow_remote=True)
        self.assertEqual('http://127.0.0.1:1234/api/v1', module.validate_native_api_base_url('http://127.0.0.1:1234/api/v1'))
        with self.assertRaises(ValueError):
            module.validate_native_api_base_url('http://127.0.0.1:1234/wrong')
        for relative in ('examples/text_request.py', 'examples/vision_request.py', 'examples/fullstack_acceptance.py', 'tests/api_smoke_test.py'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('validate_api_base_url', text, relative)
            self.assertIn('--allow-remote-base-url', text, relative)

    def test_api_authentication_is_enforced_without_token_in_process_arguments(self):
        defaults = (ROOT / 'config/defaults.conf').read_text(encoding='utf-8')
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        start = (ROOT / 'scripts/start_server.sh').read_text(encoding='utf-8')
        verifier = (ROOT / 'scripts/verify_api_auth.sh').read_text(encoding='utf-8')
        status = (ROOT / 'scripts/status.sh').read_text(encoding='utf-8')
        mcp = (ROOT / 'examples/mcp_request.sh').read_text(encoding='utf-8')
        self.assertIn('REQUIRE_API_AUTH=1', defaults)
        self.assertIn('require_secure_target_profile_config', common)
        self.assertIn('create_curl_auth_header_file()', common)
        self.assertIn('verify_api_auth.sh', start)
        self.assertIn('cleanup_failed_start()', start)
        self.assertIn('assert_lms_server_stopped 1', start)
        self.assertIn('lms server stop', start)
        self.assertIn('require_secure_target_profile_config', status)
        self.assertIn('require_api_token', status)
        self.assertIn('umask 077', mcp)
        self.assertIn('unauthenticated_code', verifier)
        self.assertIn('401|403', verifier)
        self.assertIn('--header "@$header_file"', verifier)
        self.assertNotIn('-H "Authorization: Bearer $LM_API_TOKEN"', status)
        self.assertNotIn('-H "Authorization: Bearer ${LM_API_TOKEN}"', mcp)

    def test_failed_server_postconditions_trigger_startup_rollback(self):
        with tempfile.TemporaryDirectory(prefix='gemmam5-start-rollback-') as temporary:
            bindir = Path(temporary) / 'bin'
            bindir.mkdir()
            stopped = Path(temporary) / 'stopped'
            fake_uname = bindir / 'uname'
            fake_uname.write_text('#!/usr/bin/env bash\nprintf "Darwin\n"\n', encoding='utf-8')
            fake_lsof = bindir / 'lsof'
            fake_lsof.write_text('#!/usr/bin/env bash\nprintf "n127.0.0.1:1234\n"\n', encoding='utf-8')
            fake_lms = bindir / 'lms'
            fake_lms.write_text(
                '#!/usr/bin/env bash\n'
                'if [ "$1 $2 $3" = "server status --json" ]; then\n'
                '  if [ -f "$STOP_MARKER" ]; then printf "{\\"running\\":false,\\"port\\":1234}\n"; else printf "{\\"running\\":false,\\"port\\":1234}\n"; fi; exit 0\n'
                'fi\n'
                'if [ "$1 $2 $3" = "server start --help" ]; then printf "%s\n" "--bind"; exit 0; fi\n'
                'if [ "$1 $2" = "server start" ]; then exit 0; fi\n'
                'if [ "$1 $2" = "server stop" ]; then : > "$STOP_MARKER"; exit 0; fi\n'
                'exit 0\n', encoding='utf-8')
            fake_curl = bindir / 'curl'
            fake_curl.write_text('#!/usr/bin/env bash\nprintf "200"\n', encoding='utf-8')
            for path in (fake_uname, fake_lsof, fake_lms, fake_curl):
                path.chmod(0o755)
            environment = os.environ.copy()
            environment['PATH'] = f'{bindir}:{environment["PATH"]}'
            environment['STOP_MARKER'] = str(stopped)
            environment['LM_API_TOKEN'] = 'test-token-not-a-real-secret'
            result = subprocess.run(
                ['./scripts/start_server.sh'], cwd=ROOT, env=environment, check=False, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(stopped.exists(), result.stdout + result.stderr)
            self.assertIn('stopping the server started by this script', result.stderr)

    def test_stop_and_status_are_fail_closed(self):
        stop = (ROOT / 'scripts/stop_server.sh').read_text(encoding='utf-8')
        status = (ROOT / 'scripts/status.sh').read_text(encoding='utf-8')
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        self.assertIn('assert_lms_server_stopped 10', stop)
        self.assertIn('assert_no_tcp_listener "$port" 10', stop)
        self.assertIn('Unknown argument', stop)
        self.assertIn('assert_no_tcp_listener()', common)
        self.assertIn('--connect-timeout 5', status)
        self.assertIn('--max-time 30', status)
        self.assertNotIn('|| true', status.split('log "API model list"', 1)[1])

    def test_release_guard_requires_origin_main_ci_and_exact_tag(self):
        script = (ROOT / 'scripts/create_github_release.sh').read_text(encoding='utf-8')
        for expected in ('verify_git_inventory.sh" --require-clean', 'git ls-remote --exit-code origin refs/heads/main', 'Local HEAD', 'gh run list', 'completed/success', 'git rev-list -n 1 "$tag"', 'Remote tag', 'gh release create', '--verify-tag', 'gh release view', 'isDraft', 'assets', 'execute=0'):
            self.assertIn(expected, script)
        for relative in ('docs/RELEASE.md', 'docs/ru/RELEASE.md'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('./scripts/create_github_release.sh', text, relative)
            self.assertIn('./scripts/create_github_release.sh --execute', text, relative)

    def test_github_repository_postcondition_validator(self):
        verifier = ROOT / 'scripts/verify_github_repository.py'
        payload = {
            'nameWithOwner': 'Gendalf71/GemmaM5-1-FullStack',
            'visibility': 'PUBLIC',
            'isArchived': False,
            'description': 'canonical',
            'defaultBranchRef': {'name': 'main'},
            'repositoryTopics': ['gemma-4', 'm5'],
        }
        command = [str(verifier), '--expected-name', payload['nameWithOwner'], '--expected-visibility', 'public', '--expected-description', 'canonical', '--expected-default-branch', 'main', '--expected-topic', 'gemma-4', '--expected-topic', 'm5']
        accepted = subprocess.run(command, input=json.dumps(payload), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        wrong = dict(payload)
        wrong['nameWithOwner'] = 'Other/Repo'
        rejected = subprocess.run(command, input=json.dumps(wrong), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, rejected.returncode)
        missing_topic = dict(payload)
        missing_topic['repositoryTopics'] = ['gemma-4']
        topic_rejected = subprocess.run(command, input=json.dumps(missing_topic), text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(0, topic_rejected.returncode)
        self.assertIn('missing canonical topics', topic_rejected.stderr)
        self.assertNotEqual(0, rejected.returncode)

    def test_release_postcondition_validator_rejects_missing_assets_and_drafts(self):
        verifier = ROOT / 'scripts/verify_github_release.py'
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        command = [
            str(verifier), '--expected-tag', f'v{version}',
            '--archive-name', f'GemmaM5-1-FullStack-{version}.zip',
            '--sidecar-name', f'GemmaM5-1-FullStack-{version}.zip.sha256',
        ]
        valid = {
            'tagName': f'v{version}', 'isDraft': False, 'isPrerelease': False,
            'assets': [
                {'name': f'GemmaM5-1-FullStack-{version}.zip'},
                {'name': f'GemmaM5-1-FullStack-{version}.zip.sha256'},
            ],
        }
        accepted = subprocess.run(
            command, input=json.dumps(valid), text=True, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        self.assertIn('postcondition verified', accepted.stdout)

        missing = dict(valid)
        missing['assets'] = [{'name': f'GemmaM5-1-FullStack-{version}.zip'}]
        rejected = subprocess.run(
            command, input=json.dumps(missing), text=True, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn('missing assets', rejected.stderr)

        draft = dict(valid)
        draft['isDraft'] = True
        rejected_draft = subprocess.run(
            command, input=json.dumps(draft), text=True, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertNotEqual(0, rejected_draft.returncode)
        self.assertIn('not a published stable release', rejected_draft.stderr)

    def test_all_listener_endpoints_must_be_loopback(self):
        common = (ROOT / 'scripts/lib/common.sh').read_text(encoding='utf-8')
        self.assertIn('ipaddress.ip_address(host)', common)
        self.assertIn('if not address.is_loopback', common)
        self.assertIn('lsof -nP -F n', common)



    def test_visual_assets_have_machine_checked_safe_margins(self):
        manifest = json.loads((ROOT / 'docs/assets/assets-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(VERSION, manifest['repository_version'])
        self.assertEqual(4, len(manifest['assets']))
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/validate_png_assets.py'), str(ROOT / 'docs/assets/assets-manifest.json')],
            check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('Visual assets verified: 4', result.stdout)

    def test_hardware_report_is_private_and_does_not_claim_a_benchmark(self):
        script = (ROOT / 'scripts/capture_hardware_report.sh').read_text(encoding='utf-8')
        self.assertIn('umask 077', script)
        self.assertIn('chmod 600', script)
        self.assertIn('review and redact before publication', script)
        self.assertIn('artifacts', script)
        self.assertNotIn('serial_number', script.lower())
        self.assertNotIn('ioreg', script.lower())

    def test_fullstack_acceptance_is_bounded_and_shell_free(self):
        source = (ROOT / 'examples/fullstack_acceptance.py').read_text(encoding='utf-8')
        for token in ('MAX_DOCUMENT_BYTES', 'MAX_IMAGE_BYTES', 'MAX_DOCUMENT_CHARACTERS', 'validate_memory_pressure_call', 'fixed_memory_pressure', '--allow-remote-base-url'):
            self.assertIn(token, source)
        self.assertNotIn('shell=True', source)
        self.assertIn("{'type': 'image_url'", source)
        self.assertIn("{'type': 'text'", source)
        self.assertLess(source.index("{'type': 'image_url'"), source.index("{'type': 'text'"))
        self.assertIn('This is not a general RAG engine', source)

    def test_benchmark_protocol_requires_repeatable_measured_evidence(self):
        template = json.loads((ROOT / 'benchmarks/m5-air-24gb.template.json').read_text(encoding='utf-8'))
        self.assertEqual('not_measured', template['status'])
        self.assertTrue(all(value is None for value in template['protocol'].values()))
        for key in ('prefill_tokens_per_second', 'decode_tokens_per_second'):
            self.assertIsNone(template['performance'][key])
        validator = (ROOT / 'scripts/validate_benchmark.py').read_text(encoding='utf-8')
        self.assertIn('run_count < 3', validator)
        self.assertIn("re.fullmatch(r'[0-9a-f]{64}'", validator)

    def test_backend_portability_does_not_overclaim_support(self):
        for relative in ('docs/BACKEND_PORTABILITY.md', 'docs/ru/BACKEND_PORTABILITY.md'):
            body = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn(VERSION, body)
            self.assertIn('LM Studio', body)
            self.assertTrue('not audited' in body.lower() or 'не прошли аудит' in body.lower())

    def test_external_evidence_covers_model_hardware_and_runtime_boundaries(self):
        evidence = json.loads((ROOT / EVIDENCE_RELATIVE).read_text(encoding='utf-8'))
        ids = {item['id'] for item in evidence['sources']}
        for required in ('google-gemma4-model-card', 'apple-m5-air-13', 'apple-m5-air-15', 'lmstudio-authentication', 'lmstudio-parallel-requests', 'lmstudio-rest-api'):
            self.assertIn(required, ids)

    def test_screenshot_evidence_remains_explicitly_uncaptured(self):
        template = json.loads((ROOT / 'docs/screenshot-manifest.template.json').read_text(encoding='utf-8'))
        self.assertEqual(VERSION, template['repository_version'])
        self.assertEqual('not_captured', template['status'])
        self.assertEqual([], template['files'])
        self.assertIsNone(template['redaction_reviewed'])


if __name__ == '__main__':
    unittest.main()
