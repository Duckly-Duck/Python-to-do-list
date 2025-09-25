#!/bin/bash

# This script tells Render how to build our app.
# Exit immediately if a command exits with a non-zero status.
set -o errexit

# Install the dependencies from requirements.txt
pip install -r requirements.txt