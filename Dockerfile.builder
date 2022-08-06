
FROM python:3.8-slim AS builder

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc libpq-dev
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install wheel

COPY setup.py .
COPY setup.cfg .

COPY ./aggregator/ ./aggregator
COPY ./models/ ./models
COPY ./tests/ ./tests

RUN python setup.py install
RUN pip install .