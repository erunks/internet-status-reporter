#!/bin/bash
poetry run python -m coverage run --source=. -m unittest -v src/tests/*_test.py &&
poetry run python -m coverage xml &&
poetry run python -m coverage html
