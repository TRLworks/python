#!/bin/bash

cd "$(dirname $0)"
set -e

VIRTUALENV_DIR="$HOME/.virtualenvs/rm-automation"
LOG_FILE=start_me.log

echo "[$date] $0" >> "$LOG_FILE"

echo "* create python virutal environment"
virtualenv "$VIRTUALENV_DIR" >> "$LOG_FILE" 2>&1
source "$VIRTUALENV_DIR/bin/activate"

echo "* install python dependencies (logs: $(pwd)/$LOG_FILE)"

pip install --upgrade pip >> "$LOG_FILE" 2>&1
pip install --upgrade -r requirements.txt >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo
echo "now execute: source $VIRTUALENV_DIR/bin/activate"
