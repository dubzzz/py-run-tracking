#!/usr/bin/python
#-*- coding: utf-8 -*-

# This script has to import an existing *.tcx file
# into the sqlite database
#
# Requirements (import from):
#   -  sqlite3
#   -  xml
#
# Requirements:
#   -  sqlite database have already been generated using generate_db.py
#
# Syntax:
#   ./import_tcx.py <*.pyx file>

from __future__ import print_function

import sqlite3
from xml.dom import minidom

import sys
from generate_db import DEFAULT_DB

def import_activity_from_tcxxml(activitydom, creator=None, db=DEFAULT_DB):
    r"""
    Import a run/activity from activity-dom to <db>
    
    TCX structure (inside <Activity/>):
      <Lap StartTime="yyyy-mm-ddTHH:mm:ss.MMMZ">
        <TotalTimeSeconds>(...)</TotalTimeSeconds>
        <DistanceMeters>(...)</DistanceMeters>
        <Calories>(...)</Calories>
        <Track>
          <Trackpoint>
            <Time>yyyy-mm-ddTHH:mm:ss.MMMZ</Time>
            <DistanceMeters>(...)</DistanceMeters>
            <AltitudeMeters>(...)</AltitudeMeters>
            <Position>
              <LatitudeDegrees>(...)</LatitudeDegrees>
              <LongitudeDegrees>(...)</LongitudeDegrees>
            </Position>
          </Trackpoint>
          <...>
          <Trackpoint\>
        </Track>
      </Lap>
    """
    
    print(''' - Analyse activity''')
    print(''' - - Connect to the database''')
    conn = sqlite3.connect(db)
    with conn:
        c = conn.cursor()
        
        lap = activitydom.getElementsByTagName("Lap")[0]
        start_time = lap.attributes["StartTime"].value
        time_s = lap.getElementsByTagName("TotalTimeSeconds")[0] \
                .childNodes[0].data
        distance_m = lap.getElementsByTagName("DistanceMeters")[0] \
                .childNodes[0].data
        calories = lap.getElementsByTagName("Calories")[0] \
                .childNodes[0].data
        trackpoints = lap.getElementsByTagName("Trackpoint")
        print(''' - - Activity details:''')
        print(''' - - - Start time: {}'''.format(start_time))
        print(''' - - - Time: {} seconds'''.format(time_s))
        print(''' - - - Distance: {} meters'''.format(distance_m))
        print(''' - - - Calories: {} kcal'''.format(calories))
        print(''' - - - {} track points'''.format(len(trackpoints)))
        
        c.execute('''INSERT INTO runs (start_time, time_s, distance_m,
                        calories, creator)
                        VALUES (?,?,?,?,?)''',
                (start_time, time_s, distance_m, calories, creator))
        c.execute('''SELECT id FROM runs
                        ORDER BY id DESC
                        LIMIT 1''')
        run_id = c.fetchone()[0]
        print(''' - - Id in database: {}'''.format(run_id))
        
        num_pts_analysed = 0
        num_pts = len(trackpoints)
        for tp in trackpoints:
            num_pts_analysed += 1
            print(''' - - Analyse track points ({}/{})''' \
                    .format(num_pts_analysed, num_pts), end='\r')
            
            tp_datetime = tp.getElementsByTagName("Time")[0] \
                    .childNodes[0].data
            tp_distance_m = tp.getElementsByTagName("DistanceMeters")[0] \
                    .childNodes[0].data
            tp_altitude_m = tp.getElementsByTagName("AltitudeMeters")[0] \
                    .childNodes[0].data
            
            tp_position = tp.getElementsByTagName("Position")[0]
            tp_latitude_d = tp_position \
                    .getElementsByTagName("LatitudeDegrees")[0] \
                    .childNodes[0].data
            tp_longitude_d = tp_position \
                    .getElementsByTagName("LongitudeDegrees")[0] \
                    .childNodes[0].data
            
            c.execute('''INSERT INTO points (run_id, datetime, latitude_d,
                            longitude_d, altitude_m, distance_m)
                            VALUES (?,?,?,?,?,?)''',
                    (run_id, tp_datetime, tp_latitude_d, tp_longitude_d,
                    tp_altitude_m, tp_distance_m))
        
        print(''' - - Analyse track points''')
        print(''' - - Update the database''')
        conn.commit()

def import_from_tcx(tcx_filename, db=DEFAULT_DB):
    r"""
    Import run(s) data from a *.tcx file
    Everything is stored into <db>
    
    TCX structure:
      <?xml version="1.0" encoding="UTF-8"?>
      <TrainingCenterDatabase (creator="...")>
        <Activities>
          <Activity>
            <!--
              more details in
              import_activity_from_tcxxml
            -->
          </Activity>
        </Activities>
      </TrainingCenterDatabase>
    """
    
    print('''IMPORT DATA FROM TCX: {}'''.format(tcx_filename))
    print(''' - Parse XML content''')
    xmldoc = minidom.parse(tcx_filename)
    print(''' - Look for creator's name''')
    try:
        creator = xmldoc.getElementsByTagName("TrainingCenterDatabase")[0] \
                .attributes["creator"].value
    except KeyError:
        creator = None
    print(''' - - Creator: {}'''.format(creator))
    print(''' - Look for activities''')
    activities = xmldoc.getElementsByTagName("Activity")
    print(''' - - {} activity(ies) found'''.format(len(activities)))
    for activity in activities:
        import_activity_from_tcxxml(activity, creator, db)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('''Syntax: ./import.py <*.pyx file>''')
        exit(1)
    
    # Get *.tcx filename
    tcx_filename = sys.argv[1]
    
    # Import *.tcx file
    import_from_tcx(tcx_filename, DEFAULT_DB)
