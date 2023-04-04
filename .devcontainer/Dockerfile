FROM mcr.microsoft.com/devcontainers/python:0-3.10

ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip && \
    pip install --upgrade poetry

RUN poetry config virtualenvs.in-project true
