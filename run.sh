#!/bin/bash
apt-get update && 
apt-get install -y libpq-dev &&
cd etl-python/ &&
pip install -r requirements.txt &&
python -u write_data.py
