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
    diff32 = (pt3[0]-pt2[0], pt3[1]-pt2[1], pt3[2]-pt2[0])
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
    
    # Check if the final distance reached in the run is correct
    final_distance = run_pts[current_in_run -1][2] - init_dist_run
    if final_distance < (1-MAX_ERROR_DISTANCE_RATIO)*total_dist_section \
            or final_distance > (1+MAX_ERROR_DISTANCE_RATIO)*total_dist_section:
        #print(''' - - - Bad distance ({} expected {})'''
        #        .format(final_distance, total_dist_section))
        return None
    
    # Check if average distance is ok
    avg_error = run_to_section/(current_in_run-start_at)
    if avg_error > AVG_ERROR_POINT:
        #print(''' - - - Average error per point too high ({} expected {})'''
        #        .format(avg_error, AVG_ERROR_POINT))
        return None
    
    return {"start": start_at, "end": current_in_run -1,
            "error": avg_error}

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
        print(''' - Found from {} to {} with error of {}'''
                .format(pt["start"], pt["end"], pt["error"]))
        
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
        
def find_section_in_run_db(section_id, run_id, db=DEFAULT_DB):
    r"""
    Try to recognize a section (one or several times)
    in a given run
    
    This function reads the DB to get relevant data from section and run
    """
    
    print('''FIND SECTION IN RUN (database)''')
    print(''' - Connect to the database''')
    conn = sqlite3.connect(db)
    with conn:
        c = conn.cursor()
        
        print(''' - Retrieve run points''')
        c.execute('''SELECT latitude_d, longitude_d, distance_m, id
                        FROM points
                        WHERE run_id=?''', (run_id,))
        run_pts = c.fetchall()
        
        print(''' - Retrieve section points''')
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
        section_pts = c.fetchall()
        
        selected_starting_pts = find_section_in_run(section_pts, run_pts)
        
        # Add these choices to the db
        for pt in selected_starting_pts:
            print(''' - Selected from {} to {} with error of {}'''
                    .format(pt["start"], pt["end"], pt["error"]))
            c.execute('''INSERT INTO section_run (section_id, run_id, from_id, to_id)
                            VALUES (?,?,?,?)''', (section_id, run_id,
                    pt["start"]+run_pts[0][3], pt["end"]+run_pts[0][3]))
        
        if len(selected_starting_pts) > 0:
            conn.commit()
    
        
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('''Syntax: ./find_section_in_run.py <section_id> <run_id>''')
        exit(1)
    
    try:
        section_id = int(sys.argv[1])
        run_id = int(sys.argv[2])
    except TypeError, e:
        print("ERROR: " + e)
        print('''Syntax: ./find_section_in_run.py <section_id> <run_id>''')
        exit(2)
    except ValueError, e:
        print("ERROR: " + e)
        print('''Syntax: ./find_section_in_run.py <section_id> <run_id>''')
        exit(2)
    
    # Try to recognize the section in the run
    find_section_in_run_db(section_id, run_id, DEFAULT_DB)
