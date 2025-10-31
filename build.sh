#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python -c "
from app import init_db
init_db()
print('Database initialized!')
"

# Import historical data
python import_all_data.py

