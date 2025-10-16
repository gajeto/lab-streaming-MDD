# Build a temporary image just to get requirements from UV, so that
# application image doesn't have to contain the extra build dependencies
FROM python:3.12-slim AS requirements-stage

ARG SOURCE
ARG DESTINATION


WORKDIR /tmp

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY ${SOURCE} ${DESTINATION}

RUN uv export --script ${DESTINATION} --format requirements-txt > requirements.txt


# Build the image that will be used to serve the application, which would only
# contain the necessary dependencies to run the code
FROM python:3.12-slim

WORKDIR /app

COPY --from=requirements-stage /tmp/requirements.txt ./
COPY --from=requirements-stage /tmp/${DESTINATION} ./${DESTINATION}

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
