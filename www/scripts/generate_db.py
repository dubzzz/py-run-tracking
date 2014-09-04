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
        #c.execute('''DROP TABLE IF EXISTS runs''')
        #c.execute('''DROP TABLE IF EXISTS points''')
        #c.execute('''DROP TABLE IF EXISTS sections''')
        #c.execute('''DROP TABLE IF EXISTS section_run''')
        #c.execute('''DROP TABLE IF EXISTS analyse_section_run''')
        c.execute('''DROP TABLE IF EXISTS high_scores_list''')
        c.execute('''DROP TABLE IF EXISTS high_scores_details''')
        
        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS runs (
                        id INTEGER PRIMARY KEY,
                        start_time TEXT,
                        time_s INTEGER,
                        distance_m INTEGER,
                        calories INTEGER,
                        creator TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS points (
                        id INTEGER PRIMARY KEY,
                        run_id INTEGER,
                        datetime TEXT,
                        latitude_d REAL,
                        longitude_d REAL,
                        altitude_m REAL,
                        distance_m INTEGER,
                        FOREIGN KEY(run_id) REFERENCES runs(id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS sections (
                        id INTEGER PRIMARY KEY,
                        name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS section_run (
                        id INTEGER PRIMARY KEY,
                        section_id INTEGER,
                        run_id INTEGER,
                        from_id INTEGER,
                        to_id INTEGER,
                        FOREIGN KEY(section_id) REFERENCES sections(id),
                        FOREIGN KEY(run_id) REFERENCES runs(id),
                        FOREIGN KEY(from_id) REFERENCES points(id),
                        FOREIGN KEY(to_id) REFERENCES points(id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS analyse_section_run (
                        id INTEGER PRIMARY KEY,
                        section_id INTEGER,
                        run_id INTEGER,
                        FOREIGN KEY(section_id) REFERENCES sections(id),
                        FOREIGN KEY(run_id) REFERENCES runs(id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS high_scores_details (
                        id INTEGER PRIMARY KEY,
                        is_distance BOOLEAN,
                        value INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS high_scores_list (
                        id INTEGER PRIMARY KEY,
                        high_id INTEGER,
                        run_id INTEGER,
                        from_f REAL,
                        to_f REAL,
                        score INTEGER,
                        FOREIGN KEY(high_id) REFERENCES high_scores_details(id),
                        FOREIGN KEY(run_id) REFERENCES runs(id))''')
        high_scores_details_init = (
                (1, 0, 720), # Cooper (12min)
                (2, 0, 3600), # One-hour run
                (3, 1, 1000), # 1km
                (4, 1, 5000), # 5km
                (5, 1, 10000), # 10km
                (6, 1, 21100), # Half-marathon
                (7, 1, 42195), # Marathon
        )
        c.executemany('''INSERT INTO high_scores_details (id, is_distance, value)
                            VALUES (?,?,?)''', high_scores_details_init)
        
        # Commit the changes
        conn.commit()

if __name__ == '__main__':
    generate_tables(DEFAULT_DB)
