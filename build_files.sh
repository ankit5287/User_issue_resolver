#!/usr/bin/env bash
echo "Building project and collecting static files..."

# Always ensure target output directory exists first
mkdir -p staticfiles_build/static

# Install dependencies using python3/pip
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Add python user site-packages and working directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(python3 -m site --user-site):.

# Collect static files
python3 manage.py collectstatic --noinput --clear

echo "Build completed successfully."
