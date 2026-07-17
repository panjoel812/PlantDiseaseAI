from pathlib import Path


def test_container_context_ignore_excludes_data_outputs_weights_and_secrets() -> None:
    patterns = set(Path(".dockerignore").read_text(encoding="utf-8").splitlines())

    assert "/data/" in patterns
    assert "/outputs/" in patterns
    assert ".venv/" in patterns
    assert ".env" in patterns
    assert "*.pt" in patterns
    assert ".git/" in patterns


def test_containerfile_uses_streamlit_cpu_demo_healthcheck() -> None:
    containerfile = Path("Containerfile").read_text(encoding="utf-8")

    assert "docker build -f Containerfile -t plantdisease-ai:week8 ." in containerfile
    assert "Runtime: Streamlit, CPU-only, checkpoint=/models/checkpoint.pt" in containerfile
    assert "uv pip install" in containerfile
    assert "--torch-backend cpu" in containerfile
    assert "uv sync --locked --no-dev" not in containerfile
    assert 'CMD [".venv/bin/streamlit"' in containerfile
    assert 'CMD ["uv", "run"' not in containerfile
    assert '"run", "app/streamlit_app.py"' in containerfile
    assert '"--device", "cpu"' in containerfile
    assert "HEALTHCHECK" in containerfile
