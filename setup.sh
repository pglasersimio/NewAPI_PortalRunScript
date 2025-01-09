#!/bin/bash
# setup.sh - Script to install required Python packages

echo "Installing required packages..."
pip install tenacity requests decorator
pip install -i https://test.pypi.org/simple/ pysimio>=0.0.7
echo "All packages installed successfully."
