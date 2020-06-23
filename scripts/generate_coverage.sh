#!/bin/bash
python3 -m coverage run --source=. -m unittest -v src/tests/*_test.py &&
python3 -m coverage xml &&
python3 -m coverage html
