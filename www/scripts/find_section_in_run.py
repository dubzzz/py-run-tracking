#!/usr/bin/python
#-*- coding: utf-8 -*-

# This script has to detect if a section can be found in a given run
# it is important to note that a section can be present more than one time
#
# Requirements (import from):
#   -  sqlite3
#
# Requirements:
#   -  sqlite database have already been generated using generate_db.py
#
# Syntax:
#   ./find_section_in_run.py
#   ./find_section_in_run.py <section_id> <run_id>

from __future__ import print_function

import sqlite3
import sys
from math import pi, cos, sin, sqrt
from generate_db import DEFAULT_DB

MAX_ERROR_METERS = 50.
AVG_ERROR_POINT = 10.
MAX_ERROR_DISTANCE_RATIO = 0.1
EARTH_RADIUS = 6371000

def getXYZ(latitude, longitude):
    r"""
    Convert spherical coordinates into xyz system
    """
    theta = pi*latitude/180.
    phi = pi*longitude/180.
    return (EARTH_RADIUS * sin(theta) * cos(phi),
            EARTH_RADIUS * sin(theta) * sin(phi),
            EARTH_RADIUS * cos(theta))

def getDistancePt2Pt(lat1, long1, lat2, long2):
    r"""
    Distance in meters between 2 points given as couple (lat,long)
    """
    pt1 = getXYZ(lat1, long1)
    pt2 = getXYZ(lat2, long2)
    return sqrt((pt1[0]-pt2[0])*(pt1[0]-pt2[0])
            + (pt1[1]-pt2[1])*(pt1[1]-pt2[1])
            + (pt1[2]-pt2[2])*(pt1[2]-pt2[2]))

def getScalar(pt1, pt2):
    return pt1[0]*pt2[0] + pt1[1]*pt2[1] + pt1[2]*pt2[2]

def getNorm(pt):
    return sqrt(getScalar(pt, pt))

def getCrossProduct(pt1, pt2):
    return (pt1[1]*pt2[2] - pt1[2]*pt2[1],
            pt1[2]*pt2[0] - pt1[0]*pt2[2],
            pt1[0]*pt2[1] - pt1[1]*pt2[0])

def getDistancePt2Line(lat1, long1, lat2, long2, lat3, long3):
    r"""
    Distance in meters between pt1 and the line between pt2 and pt3
    Formulas taken from:
        http://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html
    """
    
    if lat2 == lat3 and long2 == long3:
        return getDistancePt2Pt(lat1, long1, lat2, long2)
    
    pt1 = getXYZ(lat1, long1)
    pt2 = getXYZ(lat2, long2)
    pt3 = getXYZ(lat3, long3)
    
    diff12 = (pt1[0]-pt2[0], pt1[1]-pt2[1], pt1[2]-pt2[2])
    diff13 = (pt1[0]-pt3[0], pt1[1]-pt3[1], pt1[2]-pt3[2])
    diff32 = (pt3[0]-pt2[0], pt3[1]-pt2[1], pt3[2]-pt2[2])
    return getNorm(getCrossProduct(diff12, diff13))/getNorm(diff32)

def find_section_in_run_start_at(section_pts, run_pts, start_at):
    r"""
    Find some possible starting points
    """

    num_section = len(section_pts)
    num_run = len(run_pts)
    
    total_dist_section = section_pts[num_section -1][2]
    init_dist_run = run_pts[start_at][2]
    
    # Remaining distance in run is too short
    if run_pts[num_run -1][2]-init_dist_run \
            < (1-MAX_ERROR_DISTANCE_RATIO)*total_dist_section:
        #print(''' - - - Too short to contain this section''')
        return None
    
    dist_between_starts = getDistancePt2Pt(section_pts[0][0], section_pts[0][1],
            run_pts[start_at][0], run_pts[start_at][1]);
    # Difference is too high to continue
    if dist_between_starts > MAX_ERROR_METERS:
        #print(''' - - - Beginning too far from requirements ({} expected {})'''
        #        .format(dist_between_starts, MAX_ERROR_METERS))
        return None
    
    # Compute the value of the sum over the points of run
    # For each point in run, find the closest section part based on distance
    #   add the distance to this segment to run_to_section
    # The closest section part (pt1, pt2) verifies:
    #   distance pt1 < distance in run < distance pt2
    current_in_section = 0
    current_in_run = start_at +1
    run_to_section = dist_between_starts
    while current_in_run < num_run \
            and current_in_section < num_section -1:
        in_run = run_pts[current_in_run]
        distance_in_run = in_run[2] - init_dist_run
        
        # Find closest part of the section
        while current_in_section < num_section -1 \
                and distance_in_run > section_pts[current_in_section][2]:
            current_in_section += 1
        
        # Add the distance of the point to the point/line
        # To point
        if current_in_section == 0:
            to_add = getDistancePt2Pt(in_run[0], in_run[1],
                    section_pts[0][0], section_pts[0][1])
        # To point/line
        else:
            to_add = getDistancePt2Line(in_run[0], in_run[1],
                    section_pts[current_in_section-1][0], section_pts[current_in_section-1][1],
                    section_pts[current_in_section][0], section_pts[current_in_section][1])
        
        # Difference is too high to continue
        if to_add > MAX_ERROR_METERS:
            #print(''' - - - Point too far from requirements ({} expected {})'''
            #        .format(to_add, MAX_ERROR_METERS))
            return None
        run_to_section += to_add
        current_in_run += 1
    
    # Compute the value of the sum over the points of section
    # For each point in section, find the closest run part based on distance
    #   add the distance to this segment to section_to_run
    # The closest section part (pt1, pt2) verifies:
    #   distance pt1 < distance in section < distance pt2
    current_in_section = 0
    current_in_run = start_at +1
    section_to_run = dist_between_starts
    while current_in_run < num_run -1 \
            and current_in_section < num_section:
        in_section = section_pts[current_in_section]
        
        # Find closest part of the run
        while current_in_run < num_run -1 \
                and in_section[2] > run_pts[current_in_run][2] - init_dist_run:
            current_in_run += 1
        
        # Add the distance of the point to the point/line
        # To point
        if current_in_run == 0:
            to_add = getDistancePt2Pt(in_section[0], in_section[1],
                    run_pts[0][0], run_pts[0][1])
        # To point/line
        else:
            to_add = getDistancePt2Line(in_section[0], in_section[1],
                    run_pts[current_in_run-1][0], run_pts[current_in_run-1][1],
                    run_pts[current_in_run][0], run_pts[current_in_run][1])
        
        # Difference is too high to continue
        if to_add > MAX_ERROR_METERS:
            #print(''' - - - Section point too far from requirements ({} expected {})'''
            #        .format(to_add, MAX_ERROR_METERS))
            return None
        section_to_run += to_add
        current_in_section += 1
    
    # Check if the final distance reached in the run is correct
    final_distance = run_pts[current_in_run -1][2] - init_dist_run
    if final_distance < (1-MAX_ERROR_DISTANCE_RATIO)*total_dist_section \
            or final_distance > (1+MAX_ERROR_DISTANCE_RATIO)*total_dist_section:
        #print(''' - - - Bad distance ({} expected {})'''
        #        .format(final_distance, total_dist_section))
        return None
    
    # Check if average distance is ok
    avg_error_r2s = run_to_section/(current_in_run-start_at)
    avg_error_s2r = section_to_run/(current_in_run-start_at)
    avg_error = max(avg_error_r2s, avg_error_s2r)
    if avg_error > AVG_ERROR_POINT:
        #print(''' - - - Average error per point too high ({} expected {})'''
        #        .format(avg_error, AVG_ERROR_POINT))
        return None
    
    return {"start": start_at, "end": current_in_run -1,
            "error": avg_error, "error-r2s": avg_error_r2s,
            "error-s2r": avg_error_s2r}

def find_section_in_run(section_pts, run_pts, db=DEFAULT_DB):
    r"""
    Try to recognize a section (one or several times)
    in a given run
    
    Each element in section_pts and run_pts
    has to follow this rule:
        [0] is the latitude in degrees
        [1] is the longitude in degrees
        [2] is the distance from the first element
    """
    
    print('''FIND SECTION IN RUN''')
    possible_starting_pts = list()
    
    # Try all the possible starting point
    # Store the results of interesting calls
    for start_at in range(len(run_pts)):
        result_for_pt = find_section_in_run_start_at(section_pts, run_pts, start_at)
        if result_for_pt is not None:
            possible_starting_pts.append(result_for_pt)
    
    # Need to select the best choices
    # close points can lead to 2 possible starting points
    selected_starting_pts = list()
    pt_waiting_validation = None
    for pt in possible_starting_pts:
        print(''' - Found from {} to {} with error of ({},{})'''
                .format(pt["start"], pt["end"], pt["error-r2s"], pt["error-s2r"]))
        
        if pt_waiting_validation is None:
            pt_waiting_validation = pt
        # The distance between these two starting points is too high to
        # be for the same "lap"
        elif run_pts[pt["start"]][2]-run_pts[pt_waiting_validation["start"]][2] > MAX_ERROR_METERS:
            selected_starting_pts.append(pt_waiting_validation)
            pt_waiting_validation = pt
        # same "lap"
        elif pt_waiting_validation["error"] > pt["error"]:
            pt_waiting_validation = pt
    if pt_waiting_validation is not None:
        selected_starting_pts.append(pt_waiting_validation)
    
    return selected_starting_pts

def retrieve_run_pts_from_db(run_id, c):
    """r
    Get a run from the database given its id
    """
    
    print(''' - Retrieve run ({}) points'''.format(run_id))
    c.execute('''SELECT latitude_d, longitude_d, distance_m, id
                    FROM points
                    WHERE run_id=?''', (run_id,))
    return c.fetchall()

def retrieve_section_pts_from_db(section_id, c):
    print(''' - Retrieve section ({}) points'''.format(section_id))
    c.execute('''SELECT run_id, from_id, to_id FROM section_run
                    WHERE section_id=?
                    LIMIT 1''', (section_id,))
    section_details = c.fetchone()
    c.execute('''SELECT latitude_d, longitude_d, distance_m-start_distance
                    FROM
                        points,
                        (SELECT distance_m AS start_distance FROM points WHERE id=?)
                    WHERE run_id=? AND ?<=id AND id<=?''',
            (section_details[1], section_details[0], section_details[1], section_details[2],))
    return c.fetchall()

def feed_db_with_selected_section_run(section_id, section_pts,
        run_id, run_pts, selected_starting_pts, c):
    r"""
    Feed the db (cursor) with the selected starting points
    for this (section, run)
    """
    
    print(''' - Selections made for section ({}) and run ({})'''
            .format(section_id, run_id))
    for pt in selected_starting_pts:
        print(''' - - Selected from {} to {} with error of {}'''
                .format(pt["start"], pt["end"], pt["error"]))
        c.execute('''INSERT INTO section_run (section_id, run_id, from_id, to_id)
                        VALUES (?,?,?,?)''', (section_id, run_id,
                pt["start"]+run_pts[0][3], pt["end"]+run_pts[0][3]))
 
def find_section_in_run_db(section_id, run_id, db=DEFAULT_DB):
    r"""
    Try to recognize a section (one or several times)
    in a given run
    
    This function reads the DB to get relevant data from section and run
    """
    
    print('''FIND SECTION ({}) IN RUN ({}) (database)'''.format(section_id, run_id))
    print(''' - Connect to the database''')
    conn = sqlite3.connect(db)
    with conn:
        c = conn.cursor()
        
        run_pts = retrieve_run_pts_from_db(run_id, c)
        section_pts = retrieve_section_pts_from_db(section_id, c)
        selected_starting_pts = find_section_in_run(section_pts, run_pts)
        
        feed_db_with_selected_section_run(section_id, section_pts, run_id,
                run_pts, selected_starting_pts, c)
        conn.commit()

SECTION_CACHE_SIZE = 3
RUN_CACHE_SIZE = 3
def find_sections_in_runs(db=DEFAULT_DB):
    r"""
    Analyse all the (section, run) that remain to be analysed
    """
    
    print('''FIND (SECTION, RUN) to analyse (database)''')
    print(''' - Connect to the database''')
    
    # The first idea was to load all the sections and runs required and then
    # run the computation.
    # This way of doing is not suitable for large databases, for that reason
    # a cache will be responsible for storing sections and runs a short time
    conn = sqlite3.connect(db)
    with conn:
        c = conn.cursor()
        
        print(''' - Get (section, run) ids''')
        c.execute('''SELECT section_id, run_id FROM analyse_section_run
                        ORDER BY run_id, section_id''')
        section_run_ids = c.fetchall()
        
        run_cache_pointer = 0
        run_cache_ids = list()
        run_cache = list()
        for i in range(RUN_CACHE_SIZE):
            run_cache_ids.append(None)
            run_cache.append(None)
        
        section_cache_pointer = 0
        section_cache_ids = list()
        section_cache = list()
        for i in range(SECTION_CACHE_SIZE):
            section_cache_ids.append(None)
            section_cache.append(None)
        
        for (section_id, run_id) in section_run_ids:
            try:
                run_id_in_cache = run_cache_ids.index(run_id)
                run_pts = run_cache[run_id_in_cache]
            except ValueError: # not in cache
                run_pts = retrieve_run_pts_from_db(run_id, c)
                run_cache_ids[run_cache_pointer] = run_id
                run_cache[run_cache_pointer] = run_pts
                run_cache_pointer = (run_cache_pointer +1) % RUN_CACHE_SIZE
            try:
                section_id_in_cache = section_cache_ids.index(section_id)
                section_pts = section_cache[section_id_in_cache]
            except ValueError: # not in cache
                section_pts = retrieve_section_pts_from_db(section_id, c)
                section_cache_ids[section_cache_pointer] = section_id
                section_cache[section_cache_pointer] = section_pts
                section_cache_pointer = (section_cache_pointer +1) % SECTION_CACHE_SIZE
            
            selected_starting_pts = find_section_in_run(section_pts, run_pts)
            feed_db_with_selected_section_run(section_id, section_pts, run_id,
                    run_pts, selected_starting_pts, c)
        
        c.executemany('''DELETE FROM analyse_section_run
                            WHERE section_id=? AND run_id=?''', section_run_ids)
        conn.commit()
        
if __name__ == "__main__":
    num_args = len(sys.argv)
    
    # Scan the section-run to analyse
    if num_args == 1:
        find_sections_in_runs(DEFAULT_DB)
    # Scan only one section and one run
    elif num_args == 3:
        try:
            section_id = int(sys.argv[1])
            run_id = int(sys.argv[2])
        except TypeError, e:
            print("ERROR: " + e)
            print('''Syntax: ./find_section_in_run.py''')
            print('''Syntax: ./find_section_in_run.py <section_id> <run_id>''')
            exit(2)
        except ValueError, e:
            print("ERROR: " + e)
            print('''Syntax: ./find_section_in_run.py''')
            print('''Syntax: ./find_section_in_run.py <section_id> <run_id>''')
            exit(2)
        
        # Try to recognize the section in the run
        find_section_in_run_db(section_id, run_id, DEFAULT_DB)
    else:
        print('''Syntax: ./find_section_in_run.py''')
        print('''Syntax: ./find_section_in_run.py <section_id> <run_id>''')
        exit(1)

