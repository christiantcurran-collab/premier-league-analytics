#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Remove old database if exists
rm -f premier_league.db

# Initialize database with schema
python -c "
import sqlite3
with open('schema.sql', 'r') as f:
    conn = sqlite3.connect('premier_league.db')
    conn.executescript(f.read())
    conn.commit()
    conn.close()
    print('✓ Database schema created!')
"

# Import historical data
python import_all_data.py

