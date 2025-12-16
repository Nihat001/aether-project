#!/usr/bin/env bash
set -e

export PYTHONPATH=src

uvicorn aether.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
