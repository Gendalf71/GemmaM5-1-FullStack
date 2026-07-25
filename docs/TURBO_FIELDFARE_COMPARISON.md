# Structural comparison with TurboFieldfare

TurboFieldfare is used only as a benchmark for public-facing engineering documentation: a centered visual identity, concise promise, badges, quick-start links, an at-a-glance table, architecture diagrams, operational commands, scope limits, benchmark discipline and separate technical notes.

GemmaM5-1 FullStack intentionally differs in engineering purpose:

| Area | TurboFieldfare | GemmaM5-1 FullStack |
| --- | --- | --- |
| Runtime | Custom Swift and Metal inference engine | LM Studio runtime with guarded orchestration |
| Memory strategy | Streams experts from SSD | Uses the selected LM Studio GGUF package |
| Repository role | Runtime implementation and application | Installation, validation, safety and publication kit |
| Vision/tools/MCP | Text-only public runtime scope | LM Studio-mediated vision, tools and MCP profile with fail-closed examples |
| Evidence | Runtime benchmarks in the source project | Hardware claims withheld until target-Mac acceptance |

GemmaM5-1 FullStack now also enforces its single-prediction operating point with `lms load --parallel 1`; this is orchestration of an external runtime, not a custom scheduler.

No source code, logo, screenshots or prose from TurboFieldfare is copied. Similarity is limited to documentation hierarchy and evidence-first presentation.
The comparison was repeated against the public repository on 2026-07-24. The retained presentation pattern is: identity before detail, a short runnable path, an operational summary table, visible architecture, measured-versus-unmeasured separation, scope limits, technical appendices and a clear license/model boundary. GemmaM5-1 FullStack applies those principles to assurance and orchestration; it does not imitate runtime metrics or implementation claims.


Release 1.1.240 adds machine-checked visual margins, owner-evidence states and an explicit backend boundary; these are presentation/assurance improvements, not copied runtime claims.
