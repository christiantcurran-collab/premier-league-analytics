#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "=== Build Script Starting ==="

# Install Python dependencies
pip install -r requirements.txt

# Set encoding for Unicode support
export PYTHONIOENCODING=utf-8

# Remove old database if exists
rm -f premier_league.db

# Initialize database with schema
echo "Creating database schema..."
python -c "
import sqlite3
with open('schema.sql', 'r') as f:
    conn = sqlite3.connect('premier_league.db')
    conn.executescript(f.read())
    conn.commit()
    conn.close()
    print('Database schema created!')
"

# Import historical data
echo "Importing historical data..."
python import_all_data.py

echo "=== Build Complete ==="
