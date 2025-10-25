# Build a temporary image just to get requirements from UV, so that
# application image doesn't have to contain the extra build dependencies
FROM python:3.12-slim AS requirements-stage

WORKDIR /tmp

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY src/ ./src/
COPY pyproject.toml ./
COPY uv.lock ./

RUN uv build

# Build the image that will be used to serve the application, which would only
# contain the necessary dependencies to run the code
FROM python:3.12-slim

WORKDIR /app

COPY --from=requirements-stage /tmp/dist/streaming-0.1.0-py3-none-any.whl ./

RUN pip install --no-cache-dir --upgrade ./streaming-0.1.0-py3-none-any.whl

