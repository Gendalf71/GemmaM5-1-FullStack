# Backend portability boundary

Repository version: 1.1.240

The verified implementation in this release is **LM Studio only**. The exact model-resolution, load, server, authentication and postcondition scripts use the current `lms` CLI and are not portable by renaming commands.

MLX, llama.cpp and Ollama can be useful comparison or migration targets, but they are **not audited backends** of this repository. A future backend adapter must provide its own exact model identity, quantization, context, GPU/offload, concurrency, loopback/authentication, loaded-state rollback, tool boundary and benchmark evidence before it can be presented as supported.

The portable layer consists of the evidence model, safe local API policy, fixed tool validation, benchmark schema, document/vision acceptance inputs and publication workflow. Runtime-specific commands remain isolated under `scripts/`.
