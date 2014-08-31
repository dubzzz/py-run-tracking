#!/usr/bin/python

# This script has to generate the sqlite database
#
# Requirements (import from):
#   -  sqlite3
#
# Syntax:
#   ./generate_db.py

import sqlite3
DEFAULT_DB = "run-tracking.db"

def generate_tables(filename_db):
    conn = sqlite3.connect(filename_db)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE runs (
                    id INTEGER PRIMARY KEY,
                    start_time TEXT,
                    time_s INTEGER,
                    distance_m INTEGER,
                    calories INTEGER)''')
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
    #   and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    generate_tables(DEFAULT_DB)
