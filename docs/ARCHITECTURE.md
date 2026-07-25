# Architecture

GemmaM5-1 FullStack is an operational configuration around LM Studio, not a new inference runtime.

1. **Execution layer:** LM Studio, Metal acceleration, GGUF loading, KV cache and local APIs.
2. **Model layer:** Gemma 4 26B A4B QAT. The full parameter set remains addressable while MoE routing activates a subset per token.
3. **Application layer:** chat, images, document/RAG workflows, OpenAI-compatible clients and the native API.
4. **Trust layer:** host-side tool validation, MCP allowlists, local-only binding and explicit destructive confirmations.

The initial 8K context is a memory-control decision. Weight size alone does not represent unified-memory use. The repository keeps the API on `127.0.0.1` because changing the bind address creates a separate security design requiring authentication, firewall rules and client policy.

## Acceptance path (1.1.90)

`examples/fullstack_acceptance.py` sends one bounded reviewed UTF-8 excerpt and one image to the loopback OpenAI-compatible endpoint, then uses the same fixed host-validated read-only tool as the standalone tool example. It does not index documents and is not a general RAG engine.
