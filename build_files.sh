#!/usr/bin/env bash
echo "Building project and collecting static files..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
echo "Build completed successfully."
