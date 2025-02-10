#!/bin/bash
set -e

HOME_DIR="/data/ephemeral/home"

cd "$HOME_DIR/agentserver" && source "$HOME_DIR/.pyenv/versions/nlp13-env/bin/activate" && python node_generate_report.py
