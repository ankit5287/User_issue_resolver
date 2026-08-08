#!/usr/bin/env bash
echo "Building project and collecting static files..."

# Always ensure target output directory exists first
mkdir -p staticfiles_build/static

# Install requirements with --break-system-packages to comply with PEP 668 on Vercel's python environment
python3 -m pip install -r requirements.txt --break-system-packages || python3 -m pip install -r requirements.txt

# Export site-packages and working directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(python3 -m site --user-site):.

# Collect static files
python3 manage.py collectstatic --noinput --clear

echo "Build completed successfully."
