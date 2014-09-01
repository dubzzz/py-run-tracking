#!/usr/bin/python

# This script has to generate the sqlite database
#
# Requirements (import from):
#   -  sqlite3
#
# Syntax:
#   ./generate_db.py

import sqlite3

import sys
from os import path
SCRIPT_PATH = path.dirname(__file__)
DEFAULT_DB = path.join(SCRIPT_PATH, "../run-tracking.db")

def generate_tables(db=DEFAULT_DB):
    conn = sqlite3.connect(db)
    
    with conn:
        c = conn.cursor()
        
        # Drop tables if they exist
        c.execute('''DROP TABLE IF EXISTS runs''')
        c.execute('''DROP TABLE IF EXISTS points''')
        
        # Create tables
        c.execute('''CREATE TABLE runs (
                        id INTEGER PRIMARY KEY,
                        start_time TEXT,
                        time_s INTEGER,
                        distance_m INTEGER,
                        calories INTEGER,
                        creator TEXT)''')
        c.execute('''CREATE TABLE points (
                        id INTEGER PRIMARY KEY,
                        run_id INTEGER,
                        datetime TEXT,
                        latitude_d REAL,
                        longitude_d REAL,
                        altitude_m REAL,
                        distance_m INTEGER,
                        FOREIGN KEY(run_id) REFERENCES runs(id))''')
        
        # Commit the changes
        conn.commit()

if __name__ == '__main__':
    generate_tables(DEFAULT_DB)