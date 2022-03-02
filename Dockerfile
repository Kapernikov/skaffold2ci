FROM python:3.9-slim

ENV HOME=/usr/local/lib

RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=$HOME/.poetry/bin:$PATH

WORKDIR /opt/source
ADD pyproject.toml /opt/source/
ADD poetry.toml /opt/source/
ADD poetry.lock /opt/source/

RUN poetry install

ADD skaffold2ci /opt/source/skaffold2ci

RUN poetry build

FROM python:3.9-slim

ARG USER="app"
RUN useradd --create-home --shell /bin/bash $USER
WORKDIR /home/$USER
COPY --from=0 /opt/source/dist/skaffold2ci-0.1.0-py3-none-any.whl /opt/source/dist/skaffold2ci-0.1.0-py3-none-any.whl
RUN pip install /opt/source/dist/skaffold2ci-0.1.0-py3-none-any.whl
