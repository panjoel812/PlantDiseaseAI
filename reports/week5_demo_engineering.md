# Week 5 Demo Engineering Report

## Scope

This report records the Week 5 demo engineering evidence generated on
2026-07-13. The demo uses the frozen Week 3 candidate checkpoint:

- Checkpoint: `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- Model: ResNet50
- Image size: 224
- Grad-CAM target layer: `layer4.2`
- Known limitation: official PlantVillage split has known `leaf_id` overlap, and
  PlantVillage controlled-background results must not be treated as field generalization.

## Implemented Components

- UI-independent service: `src/plantdisease/serving/service.py`
- Cached service factory: `src/plantdisease/serving/cache.py`
- Disease knowledge cards: `src/plantdisease/serving/knowledge.py`
- Streamlit app: `app/streamlit_app.py`
- Fixed synthetic example: `app/examples/synthetic_leaf.png`
- Local end-to-end script: `scripts/demo_e2e.py`
- Apple container image definition: `Containerfile`
- Build context exclusions: `.dockerignore`

## Local Validation

Baseline before Week 5 changes:

```bash
uv run pytest -q
```

Result: `123 passed, 7 warnings`.

Affected tests after implementation:

```bash
uv run pytest tests/serving tests/test_streamlit_app.py tests/test_demo_e2e.py tests/test_container_config.py -q
```

The serving tests cover:

- invalid empty, corrupt, and oversized input bytes;
- Top-5 output and probability metadata;
- low-confidence warnings;
- Grad-CAM heatmap and overlay output;
- service cache identity;
- disease knowledge fallback.

Streamlit startup was checked with:

```bash
uv run streamlit run app/streamlit_app.py \
  --server.address 127.0.0.1 \
  --server.port 8505 \
  --server.headless true \
  -- \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --device cpu
```

Health probe result:

```text
ok
```

Demo screenshot:

- `reports/figures/week5_streamlit_demo.jpg`

## Fixed Example End-To-End

Command:

```bash
uv run python scripts/demo_e2e.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --image app/examples/synthetic_leaf.png \
  --output outputs/plantvillage/week5_demo/local_e2e.json \
  --overlay-output outputs/plantvillage/week5_demo/local_e2e_overlay.png \
  --device cpu \
  --top-k 5
```

Result:

- Output JSON: `outputs/plantvillage/week5_demo/local_e2e.json`
- Grad-CAM overlay: `outputs/plantvillage/week5_demo/local_e2e_overlay.png`
- Model name: `resnet50`
- Checkpoint id: `d53c09ab7fd3`
- Total local single-image time: `50.9 ms`
- Prediction time: `15.3 ms`
- Grad-CAM time: `29.6 ms`
- Top prediction on the synthetic example: `Blueberry___healthy`, probability `0.3119`

The synthetic example is not a PlantVillage test image and is not evidence of model
accuracy. It is only a fixed engineering smoke input.

## Apple Container Validation

This machine has Apple `container` CLI:

```text
container CLI version 1.1.0 (build: release, commit: 5973b9c)
```

`Containerfile` and `.dockerignore` are present and statically tested. The Apple
`container` runtime was validated on 2026-07-13 after the local Kata kernel and
Rosetta setup steps were completed.

Build and run command:

```bash
container system start --enable-kernel-install --timeout 300 && \
container build -f Containerfile -t localhost/plantdisease-ai:week5 . && \
container run --rm -p 8501:8501 \
  -v "$PWD/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42:/models" \
  localhost/plantdisease-ai:week5
```

Runtime evidence:

```text
container list
ID                                    IMAGE                            OS     ARCH   STATE    IP               CPUS  MEMORY   STARTED
7085d439-40d4-4e2a-84ca-2f4a4b2a0846  localhost/plantdisease-ai:week5  linux  arm64  running  192.168.64.4/24  4     1024 MB  2026-07-13T10:22:33Z

curl -sSf http://127.0.0.1:8501/_stcore/health
ok
```

Image and resource observations:

```text
container image inspect localhost/plantdisease-ai:week5
digest: sha256:28528ad628fc5fa7095aba0a6ef75600ca8fecff4b02b6d6a50ca7ecb783c771
platform: linux/arm64
variant size: 953,051,116 bytes (~909 MiB)

container stats 7085d439-40d4-4e2a-84ca-2f4a4b2a0846 --no-stream
Cpu %: 0.77%
Memory Usage: 821.67 MiB / 1.00 GiB
Pids: 20
```

Startup observation from `container inspect` and Streamlit logs:

```text
container creationDate: 2026-07-13T10:22:20Z
container startedDate: 2026-07-13T10:22:33Z
Uvicorn server started: 2026-07-13 10:22:34.169
Streamlit view message: 2026-07-13 10:22:36.235
```

This is a single log-derived startup observation, not a repeated cold-start benchmark.

Container-internal fixed example validation:

```bash
container exec 7085d439-40d4-4e2a-84ca-2f4a4b2a0846 \
  .venv/bin/python scripts/demo_e2e.py \
  --checkpoint /models/checkpoint.pt \
  --image app/examples/synthetic_leaf.png \
  --output /tmp/week5_container_e2e.json \
  --overlay-output /tmp/week5_container_e2e_overlay.png \
  --device cpu \
  --top-k 5
```

Result:

- Output JSON copied to `outputs/plantvillage/week5_demo/container_e2e.json`
- Grad-CAM overlay copied to `outputs/plantvillage/week5_demo/container_e2e_overlay.png`
- Model name: `resnet50`
- Checkpoint id: `d53c09ab7fd3`
- Total container single-image time: `129.8 ms`
- Prediction time: `55.4 ms`
- Grad-CAM time: `59.1 ms`
- Top prediction on the synthetic example: `Blueberry___healthy`, probability `0.3119`

Troubleshooting notes retained from validation:

- The commands are chained with `&&` so build/run will not continue if the initial
  `container system start` fails.
- The image is tagged under `localhost/` to avoid falling back to Docker Hub when the
  local image is absent.
- The `Containerfile` installs the Demo environment with
  `uv pip install --torch-backend cpu -e .`; if build output shows many `nvidia-*`
  wheels, stop that older build and rebuild from the updated branch.
- If the BuildKit bootstrap fails with `Rosetta is not installed`, install Rosetta 2
  first with `/usr/sbin/softwareupdate --install-rosetta --agree-to-license`.

## Safety Notes

The demo is a closed-set PlantVillage classifier. It cannot reliably detect unknown
diseases, non-leaf images, or field conditions. UI results include educational-use and
PlantVillage-domain warnings, and low-confidence predictions add an extra warning.
Disease knowledge cards are intentionally non-prescriptive and do not provide pesticide
names, dosage, or regulatory instructions.
