# Hardware acceptance results

This directory contains no claimed benchmark. The canonical result for `Gendalf71/GemmaM5-1-FullStack` may be populated only by the repository owner after direct measurements on the target MacBook Air M5 with 24 GB unified memory.

Copy `m5-air-24gb.template.json`, rename it with the UTC date, and replace only values actually measured on that computer. Keep the exact model key, quantization, LM Studio/runtime version, context, prompt, thermal condition and memory-pressure state with every result. Do not infer missing numbers from another Mac or from a memory estimator.

Third-party measurements remain welcome, but they must be submitted separately and labelled with their own hardware and software provenance; they must not overwrite the owner's canonical M5 Air record.

Validate a record before publication:

```bash
python3 scripts/validate_benchmark.py benchmarks/m5-air-24gb.template.json --expected-repository-version "$(cat VERSION)"
```

A measured record must contain complete software identity, exact Q4_0 model key, boolean acceptance results, positive timing/token metrics and non-negative swap values.
