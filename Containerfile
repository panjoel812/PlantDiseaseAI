FROM ghcr.io/astral-sh/uv:0.11.23 AS uv

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TORCH_BACKEND=cpu

WORKDIR /app

COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY app ./app
COPY scripts ./scripts

RUN uv venv .venv \
    && uv pip install --python .venv/bin/python --torch-backend cpu -e .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD .venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3).read()"

# Build with Docker Engine/Desktop:
# docker build -f Containerfile -t plantdisease-ai:week8 .
# Run with a read-only checkpoint directory mounted at /models.
# Apple container uses the same Containerfile with its own build/run syntax.
# Runtime: Streamlit, CPU-only, checkpoint=/models/checkpoint.pt
CMD [".venv/bin/streamlit", "run", "app/streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--", "--checkpoint", "/models/checkpoint.pt", "--device", "cpu"]
