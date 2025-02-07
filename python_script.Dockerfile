FROM --platform=$BUILDPLATFORM python:3.12-bookworm AS poetry
ENV POETRY_HOME="/opt/poetry"

RUN python -m venv ${POETRY_HOME} \
  && ${POETRY_HOME}/bin/pip install poetry==1.8.2 \
  && ${POETRY_HOME}/bin/poetry --version

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock /app/

ARG POETRY_DEPS=main
RUN ${POETRY_HOME}/bin/poetry export -f requirements.txt --output requirements.txt --only ${POETRY_DEPS} --without-hashes

FROM python:3.12-bookworm AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update \
  && apt-get install --no-install-recommends -y gcc=4:12.2.0-3 musl-dev=1.2.3-1 libc6-dev=2.36-9+deb12u9 cmake=3.25.1-1

WORKDIR /app

COPY --from=poetry /app/requirements.txt /app/requirements.txt

RUN python -m venv env \
  && source env/bin/activate \
  && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim-bookworm AS run

WORKDIR /app
COPY energy_box_control /app/energy_box_control

COPY --from=builder /app/env /app/env
COPY --from=poetry /app/requirements.txt /app/requirements.txt

ENTRYPOINT ["/app/env/bin/python", "-m"]
