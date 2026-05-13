FROM python:3.12-alpine

# gcc, musl-dev, libffi-dev are build-time deps for compiling Python packages
# with native extensions (e.g. uvicorn's websocket support via Cython).
RUN apk add --no-cache git gcc musl-dev libffi-dev

# Pre-install Python toolchain and todo-app dependencies.
# The sandbox runs with --network none, so pip install at runtime will fail;
# everything must be baked into the image.
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.32" \
    pydantic \
    pytest \
    pytest-asyncio \
    httpx \
    mypy

WORKDIR /workspace
