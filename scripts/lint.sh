#!/bin/sh
set -e
ruff format --check .
ruff check .
