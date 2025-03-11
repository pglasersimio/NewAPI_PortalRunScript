#!/bin/bash
# setup.sh - Script to install required Python packages

echo "Installing required packages..."
pip install load_dotenv tenacity requests decorator pysimio
echo "All packages installed successfully."
