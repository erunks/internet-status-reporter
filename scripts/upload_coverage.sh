#!/bin/bash
bash <(curl -Ls https://coverage.codacy.com/get.sh) report -l Python -r coverage.xml
