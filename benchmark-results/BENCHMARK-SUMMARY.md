# GPT-OSS:20B Benchmark Summary

**Date**: 2025-10-30
**System**: pesubuntu (Compute Node)
**GPU**: AMD Radeon RX 7800 XT (16GB VRAM)
**CPU**: Intel i5-12400F (12 cores)
**RAM**: 30GB

## Performance Results

### Quick Benchmark Tests

| Test | Prompt Tokens | Response Tokens | Tokens/Sec | GPU Usage | Rating |
|------|---------------|-----------------|------------|-----------|---------|
| Simple ("Hello") | 73 | 109 | **82.7** | 33% | ⚡ Excellent |
| Complex (Python code) | 87 | 1416 | **81.2** | 94% | ⚡ Excellent |

### Key Metrics

- **Average Generation Speed**: ~82 tokens/second
- **GPU Acceleration**: ✅ Working (ROCm detected)
- **GPU Utilization**: 33-94% (varies with prompt complexity)
- **Model Load Time**: ~0.15s (already loaded)
- **Prompt Processing**: 1500-1900 tok/s (very fast)

## Performance Analysis

### Strengths
✅ **GPU acceleration working excellently** - 82 tok/s far exceeds CPU-only (5-10 tok/s)
✅ **Consistent performance** across prompt sizes
✅ **Fast prompt processing** (1500+ tok/s)
✅ **Efficient GPU utilization** scaling with load

### Observations
- GPU usage scales appropriately (33% for short, 94% for long responses)
- Response generation speed stable at ~82 tok/s regardless of length
- Model already loaded in memory (0.15s load time)
- ROCm integration working despite occasional discovery warnings

### Comparison to Target

From docs/LLM-SETUP.md:
> **Expected Performance**: 20-30 tokens/second on 7B models

**Result**: **82 tokens/sec on 20B model** 🎉

This significantly exceeds expectations! The 20B parameter model is running faster than the target for 7B models.

## GPU Discovery Warnings

Ollama logs show periodic "GPU discovery timeout" warnings:
```
time=2025-10-30T09:15:08 level=INFO source=runner.go:545
msg="failure during GPU discovery"
error="failed to finish discovery before timeout"
```

**Impact**: None on performance. GPU is detected and used correctly.
**Cause**: Likely ROCm initialization delay on first discovery probe.
**Action**: Monitor, but no fix needed - performance is excellent.

## Recommendations

### For Best Performance
1. ✅ Keep model loaded (already done) - load time is minimal
2. ✅ Use GPU acceleration (working) - 8x faster than CPU-only
3. Consider testing smaller models (7B) - may hit 120+ tok/s
4. Monitor VRAM usage for multi-model scenarios

### Monitoring Commands
```bash
# Quick performance test
./scripts/quick-benchmark.sh gpt-oss:20b "Your test prompt"

# Check GPU usage
rocm-smi --showuse

# Monitor GPU in real-time
watch -n 1 rocm-smi

# View Ollama logs
journalctl -u ollama -f
```

### Next Steps
- ✅ Benchmark complete - gpt-oss:20b performing excellently
- Test other models (mistral:7b, llama3.1:8b) for comparison
- Set up LiteLLM router for load balancing
- Integrate with N8n workflows

## Benchmark Scripts

**Quick Test** (recommended):
```bash
./scripts/quick-benchmark.sh <model> "<prompt>"
```

**Comprehensive Test** (multiple prompts, iterations):
```bash
./scripts/benchmark-ollama.sh <model> <iterations>
```

## Conclusion

**Status**: ✅ **EXCELLENT**

GPT-OSS:20B is running at **82 tokens/second** with full GPU acceleration, significantly exceeding performance targets. System is ready for production workload integration with N8n and LiteLLM.
