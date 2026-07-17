# Model Efficiency Benchmark Design

## Context

Week 2 has four completed full PlantVillage official-split training runs:
MobileNetV2, ResNet18, ResNet50, and EfficientNet-B0. EfficientNetV2-S has
passed the end-to-end smoke workflow, but its full run is intentionally skipped
because the local training time is disproportionate to the remaining learning
and evidence goals.

The project must not describe this as a completed five-model full benchmark.
The defensible scope is a four-model full-run comparison plus a documented
EfficientNetV2-S smoke result and resource limitation.

## Goal

Add a reproducible `plant-benchmark` command that measures model size,
theoretical computation, inference latency, and throughput from a project
checkpoint, and saves the measurement context and raw timings as machine-readable
JSON.

## Scope

The first version will measure:

- total and trainable parameter counts;
- theoretical FLOPs for a single `1 x 3 x 224 x 224` forward pass;
- batch-1 inference latency;
- throughput at a configurable batch size;
- model, checkpoint, device, precision, input size, warmup count, measured
  iteration count, and preprocessing inclusion;
- raw per-iteration timings plus summary statistics.

Peak memory is explicitly outside this version. MPS does not provide the same
reliable peak-reset measurement workflow as CUDA, so the project will keep peak
memory marked as unmeasured instead of reporting a misleading value.

## Architecture

`src/plantdisease/evaluation/benchmark.py` will contain device-independent
parameter counting, FLOP analysis, synchronized timing, validation, and JSON
serialization. It will not know about command-line parsing.

`src/plantdisease/cli.py` will expose `benchmark_main`, which loads a checkpoint,
selects a device, delegates measurements to the evaluation module, and writes the
result. `pyproject.toml` will register it as `plant-benchmark`.

FLOP counting will use `fvcore.nn.FlopCountAnalysis`. The report will name the
tool and preserve any unsupported-operation count so theoretical computation is
not presented as exact when the analyzer cannot cover every operator.

## Measurement Protocol

The default formal protocol is:

- input size: checkpoint metadata, expected to be 224 by 224 for Week 2;
- dtype: float32;
- latency batch size: 1;
- throughput batch size: 32;
- warmup iterations: 10;
- measured iterations: 50;
- preprocessing: excluded;
- inference mode: `model.eval()` and `torch.inference_mode()`;
- device: `auto`, selecting CUDA, then MPS, then CPU;
- synchronization: before and after each timed iteration on asynchronous
  CUDA/MPS devices.

Latency will report the mean, median, sample standard deviation, minimum, maximum,
and raw milliseconds. Throughput will be calculated from total images divided by
total measured inference time and will also retain the raw batch timings.

## Input and Output

The CLI will accept one checkpoint per invocation so a failed or oversized model
does not invalidate measurements already collected for other models. Required
arguments are the checkpoint path and output JSON path. Warmup iterations,
measured iterations, throughput batch size, and device are configurable.

The JSON report will use a versioned schema and include:

- checkpoint path and checkpoint model metadata;
- hardware and software context;
- parameter statistics;
- FLOP statistics and analyzer limitations;
- latency protocol, raw samples, and summaries;
- throughput protocol, raw samples, total time, and images per second.

Invalid batch sizes, negative warmup counts, zero measured iterations, missing
checkpoints, and unavailable requested devices must fail with clear errors rather
than silently changing the protocol.

## Testing

Implementation will follow RED-GREEN-REFACTOR. Tests will cover parameter counts
with a small known model, protocol validation, synchronized timing through a
small CPU model, JSON schema/output, and CLI integration with a temporary project
checkpoint. Tests will use small tensors and short iteration counts; they will
not depend on MPS, CUDA, downloads, PlantVillage, or pretrained weights.

After focused tests pass, the full `pytest` and Ruff suites must pass. Formal JSON
artifacts will then be generated independently for the four completed full-run
checkpoints.

## Reporting and Stage Decision

The Week 2 report and task state will say that EfficientNetV2-S full training was
skipped for local resource/time reasons while its smoke result remains verified.
Only the four completed full runs may appear in the formal accuracy-efficiency
table.

The measured evidence will be used to select two Week 3 inputs:

- the best-accuracy candidate, currently expected to be ResNet50 based on completed
  test metrics;
- the deployment candidate, chosen only after parameter and speed measurements.

Week 2 may be closed as a resource-constrained four-model benchmark only after
the report, machine-readable measurements, limitations, and frozen Week 3 protocol
are complete. It must not be described as a completed five-model benchmark.
