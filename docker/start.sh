#!/usr/bin/env bash
set -e

echo "Listing contents of $(pwd):"
ls -la

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 80 --reload
