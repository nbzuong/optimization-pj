#!/bin/bash

# change dir to root of project
SCRIPT_PATH=$(dirname $0)
cd $SCRIPT_PATH/..

# execute and time it
mkdir -p scripts/output
/usr/bin/time -f "time: %Us" -ao scripts/output/CP.txt python3 drafts/CP.py > scripts/output/CP.txt
