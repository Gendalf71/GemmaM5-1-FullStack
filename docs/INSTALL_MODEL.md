# Install Gemma 4 26B A4B on a 24 GB MacBook Air M5

## 1. Operating profile

The target profile uses `google/gemma-4-26b-a4b-qat`, GGUF `Q4_0`, an initial 8,192-token context, maximum GPU offload, one concurrent prediction and the local identifier `gemma4-local`.

The official LM Studio catalog lists the selected Q4_0 package at 15.60 GB (about 14.53 GiB). That catalog/download figure is not the complete resident-memory cost, and the exact package may vary by revision. Unified memory must also hold macOS, LM Studio, the vision path, KV cache, runtime buffers and other active applications. The 256K architectural limit is therefore not a recommended local operating point.

## 2. Prepare the Mac

Connect power, keep at least 40 GB free and close memory-heavy applications.

Open the repository root. A Git clone normally uses `~/Projects/GemmaM5-1-FullStack`; the release ZIP uses the versioned directory `~/Projects/GemmaM5-1-FullStack-1.1.240`.

```bash
cd /path/to/GemmaM5-1-FullStack
chmod +x scripts/*.sh scripts/*.py examples/*.sh examples/*.py
./scripts/verify_repo.sh
./scripts/preflight.sh
```

## 3. Install LM Studio

```bash
./scripts/install_lm_studio.sh
```

Open LM Studio once, then start a fresh Terminal and run:

This profile requires LM Studio 0.4.11 or newer because that release added the updated Gemma 4 chat template required by the audited reasoning/chat path. LM Studio 0.4.20 or newer is recommended for this 1.1.240 profile. The preflight checks the application version and still verifies the actual CLI capabilities instead of trusting a version string alone.

```bash
lms --version
lms --help
lms load --help | grep -- --parallel
```

## 4. Download the exact model

```bash
./scripts/download_model.sh
lms ls --json
lms ls --variants
python3 scripts/resolve_model_identity.py --format json
```

The catalog ID and quantization are fixed for this 24 GB profile and are checked before download. Resolution reads only `lms ls --json` and requires exactly one local item that proves QAT, GGUF and `Q4_0`. It returns two separate values: `ModelInfo.path`, which is passed to `lms load --exact`, and `modelKey`, which is verified after loading. Every `MODEL_KEY` override must match that installed pair; ambiguity, remote LM Link entries and every other quantization are rejected.

## 5. Estimate before loading

```bash
./scripts/estimate_model.sh 8192
memory_pressure -Q
```

Do not continue if the estimate leaves no useful reserve or macOS already reports sustained non-green memory pressure.

## 6. Load

Dry run:

```bash
./scripts/load_model.sh
```

Actual load:

```bash
./scripts/load_model.sh --execute --context 8192
```

The command passes the resolved local path to `lms load --exact --local` and enforces `--parallel 1`. Before loading it rejects any identifier/path/modelKey collision. A no-op is permitted only for one unique already-loaded instance with the exact path, modelKey, identifier and concurrency. If loading or its postcondition fails, the script attempts a rollback with `lms unload` using the exact managed identifier.

Explicitly unload every other loaded model first, with typed confirmation:

```bash
./scripts/load_model.sh --execute --context 8192 --unload-others
```

## 7. Validate text, vision and APIs

The startup script requires an `lms` version that exposes `--bind`, requires `lsof`, waits for a bounded startup interval and rejects the server if **any** endpoint on the configured port is wildcard or non-loopback. All Python API clients reject non-loopback base URLs by default; `--allow-remote-base-url` is required before prompts, images, fixture data or `LM_API_TOKEN` may leave the machine.

```bash
./scripts/start_server.sh
python3 tests/api_smoke_test.py --model gemma4-local
python3 examples/text_request.py
python3 examples/vision_request.py
```

Stop the server with `./scripts/stop_server.sh`; shutdown is accepted only after `running=false` and disappearance of every listener on the configured port.

Use LM Studio's interface for document and RAG tests. A scanned PDF without a usable text layer may require a separate OCR step.

## 8. Tools and MCP

Run the constrained host-side tool example:

```bash
python3 examples/safe_tool_call.py
```

MCP requires LM Studio 0.4.11 or newer in this repository profile and explicit server permissions; 0.4.20 or newer is recommended. Review `docs/MCP_SAFE_PATTERNS.md` before enabling it.

## 9. Increase context only by measurement

```bash
./scripts/estimate_model.sh 12288
./scripts/estimate_model.sh 16384
```

Treat 32K and above as experimental. Return to 8K at persistent swap, unstable vision, load errors or unacceptable latency.

## 10. Record the environment

```bash
mkdir -p artifacts
./scripts/collect_environment.sh > artifacts/hardware-environment.txt
```

Complete the protocol in `docs/VALIDATION.md`. No repository claim replaces this target-Mac acceptance.

## Capture model provenance

After exact model discovery, record the installed variant without publishing local paths:

```bash
make provenance
cat artifacts/model-provenance.json
```

This is a privacy-filtered local record, not a checksum of the external weights. See [Model provenance](MODEL_PROVENANCE.md).

## Mandatory local API authentication

In LM Studio open **Developer > Server Settings**, enable **Require Authentication**, and create a least-privilege API token. Load it into the current Terminal without adding it to shell history:

```bash
read -s LM_API_TOKEN
export LM_API_TOKEN
printf '\n'
```

`start_server.sh` enforces `REQUIRE_API_AUTH=1`, proves that an unauthenticated request is rejected and that the token-authenticated request succeeds. Shell clients use an owner-only temporary header file so the token is not placed in `curl` command-line arguments.

## Exact hardware profile

`preflight.sh` does not treat every 24 GB Apple Silicon Mac as equivalent to the target. It reads machine JSON from `system_profiler` and requires `MacBook Air` plus an `M5` chip token, arm64, at least 24 GiB of reported memory and macOS 26.0 or newer. Another Mac may be compatible, but it is outside this validated profile and requires a separate configuration.

## Non-weakenable target profile

`config/local.conf` may carry reviewed local tuning or stricter thresholds. Operational scripts reject attempts to disable API authentication, lower the 24 GB memory, 35 GB free-space or macOS 26.0 floors, change the MacBook Air M5/Q4_0 target, expose the bind address or raise concurrent predictions above one.
