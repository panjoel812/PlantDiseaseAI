# Model Efficiency Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `plant-benchmark` so every trained checkpoint can produce reproducible model-size, FLOP, latency, and throughput evidence as JSON.

**Architecture:** Put benchmark logic in `src/plantdisease/evaluation/benchmark.py`; keep `src/plantdisease/cli.py` responsible only for parsing arguments and printing a compact summary. Use a versioned JSON report so Week 2 tables can be generated from machine-readable artifacts rather than hand-copied numbers.

**Tech Stack:** Python 3.12, PyTorch, torchvision checkpoints, `fvcore.nn.FlopCountAnalysis`, pytest, Ruff, uv.

## Global Constraints

- Use checkpoint metadata for model name, number of classes, and input image size.
- Default formal protocol: float32, latency batch size 1, throughput batch size 32, warmup 10, measured iterations 50.
- Device auto-selection order: CUDA, then MPS, then CPU.
- Exclude preprocessing from latency and throughput measurements.
- Synchronize CUDA and MPS before and after each timed iteration.
- Peak memory is not measured in this version; record that explicitly in the JSON.
- Invalid batch sizes, negative warmup counts, zero measured iterations, missing checkpoints, and unavailable requested devices must fail with clear errors.
- Week 2 final model choice cannot be declared until efficiency data exists.

---

## File Structure

- Create `src/plantdisease/evaluation/benchmark.py`: parameter counting, FLOP analysis, protocol validation, timing, checkpoint benchmark orchestration, JSON writing.
- Modify `src/plantdisease/cli.py`: add `benchmark_main(argv)`.
- Modify `pyproject.toml`: add `fvcore` dependency and `plant-benchmark` script entry.
- Create `tests/evaluation/test_benchmark.py`: unit and integration tests for the benchmark module.
- Create `tests/test_benchmark_cli.py`: CLI integration test.

---

### Task 1: Parameters and FLOPs

**Files:**
- Create: `src/plantdisease/evaluation/benchmark.py`
- Create: `tests/evaluation/test_benchmark.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Produces: `count_parameters(model: nn.Module) -> dict[str, int]`
- Produces: `analyze_flops(model: nn.Module, image_size: int) -> dict[str, object]`

- [ ] **Step 1: Add failing tests**

Add tests that import `plantdisease.evaluation.benchmark`, count a known two-layer model, and analyze FLOPs for a tiny convolution.

```python
def test_count_parameters_reports_total_and_trainable() -> None:
    model = nn.Sequential(nn.Linear(4, 3), nn.Linear(3, 2))
    model[1].weight.requires_grad = False

    assert count_parameters(model) == {"total": 23, "trainable": 17}


def test_analyze_flops_reports_total_and_unsupported_ops() -> None:
    model = nn.Conv2d(3, 4, kernel_size=3, padding=1)

    report = analyze_flops(model, image_size=8)

    assert report["tool"] == "fvcore.nn.FlopCountAnalysis"
    assert report["input_shape"] == [1, 3, 8, 8]
    assert report["total"] == 6912
    assert report["unsupported_ops"] == {}
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: fails because `plantdisease.evaluation.benchmark` does not exist.

- [ ] **Step 3: Add dependency**

Run: `uv add "fvcore>=0.1.5,<0.2"`

Expected: `pyproject.toml` and `uv.lock` now include `fvcore`.

- [ ] **Step 4: Implement minimal module**

Implement `count_parameters()` and `analyze_flops()` using `fvcore.nn.FlopCountAnalysis`. Convert unsupported-op counters to plain `dict[str, int]`.

- [ ] **Step 5: Verify GREEN**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: both tests pass.

---

### Task 2: Protocol Validation and Timing

**Files:**
- Modify: `src/plantdisease/evaluation/benchmark.py`
- Modify: `tests/evaluation/test_benchmark.py`

**Interfaces:**
- Produces: `validate_protocol(warmup_iterations: int, measured_iterations: int, latency_batch_size: int, throughput_batch_size: int) -> None`
- Produces: `summarize_timings_ms(samples_ms: Sequence[float]) -> dict[str, float]`
- Produces: `measure_forward(model: nn.Module, device: torch.device, batch_size: int, image_size: int, warmup_iterations: int, measured_iterations: int, dtype: torch.dtype = torch.float32) -> dict[str, object]`

- [ ] **Step 1: Add failing tests**

Add tests for invalid counts, timing summaries, and a tiny CPU forward pass.

```python
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"warmup_iterations": -1}, "warmup_iterations"),
        ({"measured_iterations": 0}, "measured_iterations"),
        ({"throughput_batch_size": 0}, "throughput_batch_size"),
    ],
)
def test_validate_protocol_rejects_invalid_values(kwargs: dict[str, int], message: str) -> None:
    params = {
        "warmup_iterations": 0,
        "measured_iterations": 1,
        "latency_batch_size": 1,
        "throughput_batch_size": 1,
    }
    params.update(kwargs)

    with pytest.raises(ValueError, match=message):
        validate_protocol(**params)


def test_summarize_timings_ms_reports_expected_statistics() -> None:
    summary = summarize_timings_ms([1.0, 3.0])

    assert summary["mean"] == pytest.approx(2.0)
    assert summary["median"] == pytest.approx(2.0)
    assert summary["stdev"] == pytest.approx(1.41421356237)
    assert summary["min"] == pytest.approx(1.0)
    assert summary["max"] == pytest.approx(3.0)


def test_measure_forward_returns_raw_timings_on_cpu() -> None:
    model = nn.Conv2d(3, 2, kernel_size=1)

    report = measure_forward(
        model,
        torch.device("cpu"),
        batch_size=1,
        image_size=8,
        warmup_iterations=0,
        measured_iterations=2,
    )

    assert report["batch_size"] == 1
    assert len(report["raw_ms"]) == 2
    assert all(sample > 0 for sample in report["raw_ms"])
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: fails because validation, summary, and timing functions do not exist.

- [ ] **Step 3: Implement validation and timing**

Use `time.perf_counter()`, `torch.inference_mode()`, `model.eval()`, and `synchronize_device()` for CUDA/MPS.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: all benchmark module tests pass.

---

### Task 3: Checkpoint JSON Report

**Files:**
- Modify: `src/plantdisease/evaluation/benchmark.py`
- Modify: `tests/evaluation/test_benchmark.py`

**Interfaces:**
- Produces: `resolve_device(requested: str) -> torch.device`
- Produces: `run_checkpoint_benchmark(checkpoint_path: Path, output_path: Path, device_name: str, warmup_iterations: int, measured_iterations: int, throughput_batch_size: int) -> dict[str, object]`

- [ ] **Step 1: Add failing tests**

Add an integration test that saves a tiny MobileNetV2 checkpoint and verifies the persisted report schema.

```python
def test_run_checkpoint_benchmark_writes_versioned_json(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    output_path = tmp_path / "benchmark.json"
    model = create_model("mobilenet_v2", num_classes=2, pretrained=False)
    save_checkpoint(
        checkpoint_path,
        model,
        class_names=["healthy", "disease"],
        config={"model_name": "mobilenet_v2", "num_classes": 2, "image_size": 64},
    )

    report = run_checkpoint_benchmark(
        checkpoint_path=checkpoint_path,
        output_path=output_path,
        device_name="cpu",
        warmup_iterations=0,
        measured_iterations=1,
        throughput_batch_size=1,
    )

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved == report
    assert saved["schema_version"] == 1
    assert saved["checkpoint"]["model_name"] == "mobilenet_v2"
    assert saved["measurement"]["preprocessing_included"] is False
    assert saved["measurement"]["peak_memory_measured"] is False
    assert saved["latency"]["batch_size"] == 1
    assert saved["throughput"]["images_per_second"] > 0
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: fails because `run_checkpoint_benchmark` does not exist.

- [ ] **Step 3: Implement checkpoint benchmark orchestration**

Load checkpoint on CPU, compute FLOPs on CPU, move the model to the requested device for timing, and write a stable JSON report with schema version 1.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/evaluation/test_benchmark.py -q`

Expected: all benchmark module tests pass.

---

### Task 4: CLI Entry Point

**Files:**
- Modify: `src/plantdisease/cli.py`
- Modify: `pyproject.toml`
- Create: `tests/test_benchmark_cli.py`

**Interfaces:**
- Consumes: `run_checkpoint_benchmark(...)`
- Produces: `benchmark_main(argv: Sequence[str] | None = None) -> None`
- Produces script: `plant-benchmark`

- [ ] **Step 1: Add failing CLI test**

Create a CLI test that calls `benchmark_main()` with a temporary checkpoint and output path.

```python
def test_benchmark_main_writes_report_and_prints_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    output_path = tmp_path / "benchmark.json"
    model = create_model("mobilenet_v2", num_classes=2, pretrained=False)
    save_checkpoint(
        checkpoint_path,
        model,
        class_names=["healthy", "disease"],
        config={"model_name": "mobilenet_v2", "num_classes": 2, "image_size": 64},
    )

    benchmark_main(
        [
            "--checkpoint",
            str(checkpoint_path),
            "--output",
            str(output_path),
            "--device",
            "cpu",
            "--warmup",
            "0",
            "--iterations",
            "1",
            "--throughput-batch-size",
            "1",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "completed"
    assert summary["model_name"] == "mobilenet_v2"
    assert output_path.exists()
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_benchmark_cli.py -q`

Expected: fails because `benchmark_main` does not exist.

- [ ] **Step 3: Implement CLI and script entry**

Add parser arguments `--checkpoint`, `--output`, `--device`, `--warmup`, `--iterations`, and `--throughput-batch-size`. Register `plant-benchmark = "plantdisease.cli:benchmark_main"`.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/test_benchmark_cli.py tests/evaluation/test_benchmark.py -q`

Expected: CLI and module tests pass.

---

### Task 5: Formal Week 2 Measurements

**Files:**
- Generate: `outputs/plantvillage/benchmarks/*.json`
- Later modify after reviewing outputs: `README.md`, `TASKS.md`, `docs/artifact-index.md`, `reports/week2_benchmark_progress.md`

**Interfaces:**
- Consumes script: `plant-benchmark`
- Produces benchmark JSON files for the five formal checkpoints.

- [ ] **Step 1: Run full verification before measurements**

Run:

```bash
uv run pytest -q
uv run ruff check .
```

Expected: pytest passes and Ruff reports no errors.

- [ ] **Step 2: Run a short probe**

Run:

```bash
uv run plant-benchmark \
  --checkpoint outputs/plantvillage/baseline_mobilenet_v2_best_seed42/checkpoint.pt \
  --output outputs/plantvillage/benchmarks/probe_mobilenet_v2.json \
  --device auto \
  --warmup 1 \
  --iterations 2 \
  --throughput-batch-size 4
```

Expected: JSON report is written and includes `schema_version = 1`.

- [ ] **Step 3: Run formal measurements**

Run one command per checkpoint with `--warmup 10 --iterations 50 --throughput-batch-size 32 --device auto`.

- [ ] **Step 4: Review before documentation**

Open the five JSON files, compare speed and size, then update docs only after confirming the generated evidence.

---

## Self-Review

- Spec coverage: parameters, trainable parameters, FLOPs, raw timings, summary statistics, device/dtype/context, preprocessing exclusion, peak-memory omission, validation failures, and CLI output are covered.
- Placeholder scan: no incomplete markers are intentionally left in this plan.
- Type consistency: all function names used in later tasks are produced by earlier tasks.
