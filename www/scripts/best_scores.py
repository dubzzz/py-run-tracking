#!/usr/bin/python
#-*- coding: utf-8 -*-

# Measuring best performances in a run is the aim of this script
#
# Requirements (import from):
#   -  sqlite3
#
# Requirements:
#   -  sqlite database have already been generated using generate_db.py
#
# Syntax:
#   ./best_scores.py <run_id>

from __future__ import print_function

import sqlite3

import sys
from generate_db import DEFAULT_DB

def get_best_score_for(details, run_pts):
    r"""
    Find and return the best score for the given details:
        (id, is_distance, value)
    Otherwise, return None
    
    run_pts are given as: (distance, time)
    
    Return is (from_f, to_f, score)
    """
    
    best_score = None
    best_from = None
    best_to = None
    
    expected_value = details[2]
    
    # For time
    if details[1] == 0:
        check_id = 1 # id to check
        save_id = 0
        is_distance = False
    # For distance
    else:
        check_id = 0
        save_id = 1
        is_distance = True
    
    # Consider all the possible starting points
    num_pts = len(run_pts)
    current_to = 0
    for current_from in range(num_pts):
        # Is it still possible to reach that time/distance from that point?
        if run_pts[num_pts-1][check_id] - run_pts[current_from][check_id] \
                < expected_value:
            break #NO
        
        # Find the first id - current_to - that satisfies:
        #   run_pts[current_to][check_id] - run_pts[current_from][check_id]
        #       >= expected_value
        # By previous check we know that such point exists
        while run_pts[current_to][check_id] - run_pts[current_from][check_id] \
                < expected_value:
            current_to += 1
        
        # if the value is equal to the expected one no problem
        if run_pts[current_to][check_id] - run_pts[current_from][check_id] \
                == expected_value:
            score = run_pts[current_to][save_id] - run_pts[current_from][save_id]
            from_f = current_from
            to_f = current_to
        # otherwise we need to reduce the interval (on the left or on the right)
        # the left part can reach at most current_from +1
        #       more will be next one job
        # for the right part to_from -1
        #       less will not meet the requirements
        else:
            # eg. We want the best on 5km, we have:
            # |1|3|3| which is 7km long
            # we can remove part#1 (left) or part#3 (right)
            
            # we can always reach the requirements by reducing on the right
            # it has been built for that
            
            # Reduce RIGHT
            # * size of the remaining part if we remove right part
            missing_right = expected_value - run_pts[current_to-1][check_id] \
                    + run_pts[current_from][check_id]
            # * size of removed part
            last_right = run_pts[current_to][check_id] - run_pts[current_to-1][check_id]
            ratio_right = float(missing_right) / float(last_right)
            score_right = run_pts[current_to-1][save_id] - run_pts[current_from][save_id] \
                    + ratio_right * (run_pts[current_to][save_id] - run_pts[current_to-1][save_id])
            
            # Reduce LEFT
            # reducing only on the left can be not enough
            # eg. target=5:
            #   |1|3|3| removing only left part will still be too much
            # if left is not enough it we be done in loop (current_from+1)
            missing_left = expected_value - run_pts[current_to][check_id] \
                    + run_pts[current_from+1][check_id]
            if missing_left > 0:
                first_left = run_pts[current_from+1][check_id] - run_pts[current_from][check_id]
                ratio_left = float(missing_left) / float(first_left)
                score_left = run_pts[current_to][save_id] - run_pts[current_from+1][save_id] \
                        + ratio_left * (run_pts[current_from+1][save_id] - run_pts[current_from][save_id])
                if is_distance != (score_left < score_right):
                    score = score_left
                    from_f = current_from +1 - ratio_left
                    to_f = current_to
                else:
                    score = score_right
                    from_f = current_from
                    to_f = current_to -1 + ratio_right
            else:
                score = score_right
                from_f = current_from
                to_f = current_to -1 + ratio_right
        
        # Is the score better than previous one?
        if best_score is None or (is_distance != (best_score < score)):
            best_score = score
            best_from = from_f
            best_to = to_f
    
    if best_score is None:
        return None
    
    return (best_from, best_to, best_score)

def update_best_scores_for_run(run_id, db=DEFAULT_DB):
    r"""
    Update the best scores for a given run
    Start by removing previous best scores
    """
    
    print('''FINDING BEST SCORES FOR RUN ({})'''.format(run_id))
    conn = sqlite3.connect(db)
    with conn:
        c = conn.cursor()
        
        # Delete previous best scores
        print(''' - Delete previous best scores for this run''')
        c.execute('''DELETE FROM best_score_lines WHERE run_id=?''', (run_id,))
        
        # Get scores to measure
        print(''' - Open best scores checklist''')
        c.execute('''SELECT id, is_distance, value FROM best_scores''')
        best_scores_details = c.fetchall()
        
        # Get the run points
        print(''' - Retrieve run points''')
        c.execute('''SELECT distance_m, (julianday(datetime)-2440587.5)*86400.0
                        FROM points WHERE run_id=?''', (run_id,))
        run_pts = c.fetchall()
        
        # Measure best scores for this run
        best_score_lines = list()
        for details in best_scores_details:
            if details[1] == 0:
                print(''' - Best score for: {} mins'''.format(details[2]/60))
            else:
                print(''' - Best score for: {} km'''.format(details[2]/1000))
            best_score = get_best_score_for(details, run_pts)
            if best_score is not None:
                if details[1] == 0:
                    print(''' - - Found {} km [{}-{}]'''
                            .format(best_score[2]/1000, best_score[0], best_score[1]))
                else:
                    print(''' - - Found {} mins [{}-{}]'''
                            .format(best_score[2]/60, best_score[0], best_score[1]))
                best_score_lines.append((details[0], run_id, best_score[0],
                        best_score[1], best_score[2],))
        c.executemany('''INSERT INTO best_score_lines (best_id, run_id,
                                from_f, to_f, score) VALUES
                            (?,?,?,?,?)''', best_score_lines)
        
        conn.commit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('''Syntax: ./import.py <run_id>''')
        exit(1)
    
    try:
        run_id = int(sys.argv[1])
    except TypeError, e:
        print('''ERROR: {}'''.format(e))
        print('''Syntax: ./import.py <run_id>''')
        exit(2)
    except ValueError, e:
        print('''ERROR: {}'''.format(e))
        print('''Syntax: ./import.py <run_id>''')
        exit(3)
    
    update_best_scores_for_run(run_id, DEFAULT_DB)

