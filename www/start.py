#!/usr/bin/python

# Launch a very light-HTTP server: Tornado
#
# Requirements (import from):
#   -  tornado
#   -  sqlite3
#
# Syntax:
#   ./start.py <port=8080>

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application, url
import sqlite3

import sys
from os import path
from threading import Thread
import uuid

WWW_PATH = path.dirname(__file__)
SCRIPT_PATH = path.join(WWW_PATH, "scripts/")
RUN_PATH = path.join(WWW_PATH, "runs/")
TEMPLATE_PATH = path.join(WWW_PATH, "templates/")
STATIC_PATH = path.join(WWW_PATH, "static/")

from keys import GOOGLE_MAPS_KEY

sys.path.append(SCRIPT_PATH)
from generate_db import DEFAULT_DB
from import_tcx import import_from_tcx
from find_section_in_run import find_sections_in_runs
from high_scores import get_high_scores_for_run

def get_template(name):
    return path.join(TEMPLATE_PATH, name+".html")

class MyRunsHandler(RequestHandler):
    def get(self):
        r""" Display all the runs stored into the database
        """
        
        my_runs = list()
        conn = sqlite3.connect(DEFAULT_DB)
        with conn:
            c = conn.cursor()
            c.execute('''SELECT (julianday(start_time)-2440587.5)*86400.0,
                                time_s, distance_m, calories, id
                            FROM runs ORDER BY date(start_time) DESC''')
            my_runs_db = c.fetchall()
            for run in my_runs_db:
                my_runs.append({'date': run[0], 'time': run[1],
                        'distance': run[2], 'calories': run[3],
                        'speed': float(run[2])/float(run[1]),
                        'id': run[4]})
            del my_runs_db
        self.render(get_template("my_runs"), page="my_runs", my_runs=my_runs)

class NewRunHandler(RequestHandler):
    def initialize(self, success=False):
        r""" Initialize the handler
        """
        self.success = success
    
    def get(self):
        r""" Display a form to add a new run into the database 
        """
        
        self.render(get_template("new_run"), page="new_run",
                success=self.success)
    
    def post(self):
        r""" Add a run to the database
        """
        try:
            runfile = self.request.files['runfile'][0]
        except KeyError:
            self.render(get_template("new_run"), page="new_run",
                    errors={'runfile': "Fichier manquant"})
            return
        
        filename = path.split(runfile['filename'])[1]
        extension = path.splitext(filename)[1]
        
        if extension != ".tcx":
            self.render(get_template("new_run"), page="new_run",
                    errors={'runfile': "Extension de fichier incorrecte, .tcx requis"})
            return
        
        fullfilename = path.join(RUN_PATH, filename)
        with open(fullfilename, 'w') as f:
            f.write(runfile['body'])
        import_from_tcx(fullfilename, DEFAULT_DB)
        
        # Try to find existing sections in this run
        Thread(target=find_sections_in_runs, args=(DEFAULT_DB,)).start()
        
        # Redirect to new run success
        self.redirect(self.reverse_url("new_run_success"))

class NewSectionHandler(RequestHandler):
    def post(self, run_id):
        r""" Add a section to the run run_id
        """
        
        section_from = int(self.request.arguments['section_from'][0])
        section_to = int(self.request.arguments['section_to'][0])
        existing_section_id = int(self.request.arguments['existing_section_id'][0])
        new_section_name = self.request.arguments['new_section_name'][0]
        
        # Bad sections from/to
        if section_from >= section_to:
            return
        
        # Retrieve real ids from points
        section_from_id = None
        section_to_id = None
        conn = sqlite3.connect(DEFAULT_DB)
        with conn:
            c = conn.cursor()
            c.execute('''SELECT * FROM (SELECT id FROM points WHERE run_id=?
                            LIMIT 1 OFFSET ?)
                         UNION
                         SELECT * FROM (SELECT id FROM points WHERE run_id=?
                            LIMIT 1 OFFSET ?)''',
                    (run_id, section_from, run_id, section_to))
            data_db = c.fetchall()
            section_from_id = data_db[0][0]
            section_to_id = data_db[1][0]
        
            # New section
            if existing_section_id == -1:
                if len(new_section_name) == 0:
                    return
                c.execute('''INSERT INTO sections (name) VALUES (?)''',
                        (new_section_name,))
                c.execute('''SELECT id FROM sections ORDER BY id DESC LIMIT 1''')
                existing_section_id = c.fetchone()[0]
                
                # The section will have to be analysed vs other runs
                c.execute('''SELECT id FROM runs WHERE id<>?''', (run_id,))
                run_ids = c.fetchall()
                for run_id_ in run_ids:
                    c.execute('''INSERT into analyse_section_run (section_id, run_id)
                                    VALUES (?,?)''', (existing_section_id, run_id_[0],))
            
            # New or old section do the same job
            c.execute('''INSERT INTO section_run (section_id, run_id,
                                from_id, to_id) VALUES (?,?,?,?)''',
                    (existing_section_id, run_id, section_from_id, section_to_id,))
            
            # Commit changes
            conn.commit()
            
            # Try to find this section in other runs
            Thread(target=find_sections_in_runs, args=(DEFAULT_DB,)).start()
            
            # Redirect towards run_sections
            self.redirect(self.reverse_url("run_sections", run_id))
        return

class RunDetailsHandler(RequestHandler):
    def get(self, run_id):
        r""" Display details concerning a given run
        """
        
        next_run = None
        previous_run = None
        
        run_details = dict()
        run_path = list()
        high_scores = list()
        conn = sqlite3.connect(DEFAULT_DB)
        with conn:
            c = conn.cursor()
            
            # Retrieve details concerning the run
            c.execute('''SELECT (julianday(start_time)-2440587.5)*86400.0,
                                time_s, distance_m, calories
                            FROM runs WHERE id=?
                            LIMIT 1''', (run_id,))
            run_details_db = c.fetchone()
            run_details = {
                    'start': run_details_db[0],
                    'time': run_details_db[1],
                    'distance': run_details_db[2],
                    'calories': run_details_db[3],
                    'speed': float(run_details_db[2])/float(run_details_db[1]),}
            del run_details_db
            
            # Get next/previous run ids (based on start_time)
            # runs may have been added without any order
            c.execute('''SELECT id, (julianday(start_time)-2440587.5)*86400.0
                            FROM runs
                            WHERE start_time>datetime(?, 'unixepoch')
                                OR (start_time=datetime(?, 'unixepoch') AND id>?)
                            ORDER BY start_time ASC, id ASC
                            LIMIT 1''',
                    (run_details['start'], run_details['start'], run_id,))
            next_run = c.fetchone()
            c.execute('''SELECT id, (julianday(start_time)-2440587.5)*86400.0
                            FROM runs
                            WHERE start_time<datetime(?, 'unixepoch')
                                OR (start_time=datetime(?, 'unixepoch') AND id<?)
                            ORDER BY start_time DESC, id DESC
                            LIMIT 1''',
                    (run_details['start'], run_details['start'], run_id,))
            previous_run = c.fetchone()
            
            # Retrieve the path
            c.execute('''SELECT latitude_d, longitude_d, altitude_m,
                                (julianday(datetime)-2440587.5)*86400.0,
                                distance_m, julianday(datetime)*86400.0-?
                            FROM points WHERE run_id=?''',
                    (run_details['start']+2440587.5*86400,run_id,))
            run_path = c.fetchall()
            
            # Get high scores
            high_scores = get_high_scores_for_run(run_id, c)
            conn.commit()
        
        self.render(get_template("run_details"), page="run_details",
                google_key=GOOGLE_MAPS_KEY, run_id=run_id,
                previous_run=previous_run, next_run=next_run,
                details=run_details,
                corresponding_ids={'latitude': 0, 'longitude': 1,
                    'altitude': 2, 'datetime': 3, 'distance': 4, 'time': 5},
                run_path=run_path, high_scores=high_scores)

class RunSectionsHandler(RequestHandler):
    def get(self, run_id):
        r""" Display sections registered in a given run
        """
        
        next_run = None
        previous_run = None
        run_path = list()
        all_sections_available = list()
        run_sections = list()
        conn = sqlite3.connect(DEFAULT_DB)
        with conn:
            c = conn.cursor()
            
            # Retrieve details concerning the run
            c.execute('''SELECT start_time
                            FROM runs WHERE id=?
                            LIMIT 1''', (run_id,))
            data_db = c.fetchone()
            
            # Get next/previous run ids (based on start_time)
            # runs may have been added without any order
            c.execute('''SELECT id, (julianday(start_time)-2440587.5)*86400.0
                            FROM runs
                            WHERE start_time>? OR (start_time=? AND id>?)
                            ORDER BY start_time ASC, id ASC
                            LIMIT 1''', (data_db[0], data_db[0], run_id,))
            next_run = c.fetchone()
            c.execute('''SELECT id, (julianday(start_time)-2440587.5)*86400.0
                            FROM runs
                            WHERE start_time<? OR (start_time=? AND id<?)
                            ORDER BY start_time DESC, id DESC
                            LIMIT 1''', (data_db[0], data_db[0], run_id,))
            previous_run = c.fetchone()
            
            # Retrieve the path
            c.execute('''SELECT latitude_d, longitude_d, altitude_m,
                                (julianday(datetime)-2440587.5)*86400.0,
                                distance_m, (julianday(datetime)-julianday(?))*86400.0, id
                            FROM points WHERE run_id=?
                            ORDER BY datetime ASC''',
                    (data_db[0],run_id,))
            run_path = c.fetchall()
            
            # Retrieve the available sections
            c.execute('''SELECT id, name FROM sections''')
            all_sections_available = c.fetchall()
            c.execute('''SELECT name, from_id-?, to_id-?
                            FROM section_run
                            INNER JOIN sections
                                ON section_run.section_id=sections.id
                            WHERE run_id=?
                            ORDER BY from_id''',
                    (run_path[0][6], run_path[0][6], run_id,))
            run_sections = c.fetchall()
        
        self.render(get_template("run_sections"), page="run_sections",
                google_key=GOOGLE_MAPS_KEY, run_id=run_id,
                previous_run=previous_run, next_run=next_run,
                corresponding_ids={'latitude': 0, 'longitude': 1,
                    'altitude': 2, 'datetime': 3, 'distance': 4, 'time': 5},
                run_path=run_path, all_sections_available=all_sections_available,
                run_sections=run_sections)

# Define tornado application
application = Application([
    url(r"/", MyRunsHandler, name="my_runs"),
    url(r"/new/run/", NewRunHandler, name="new_run"),
    url(r"/new/run/s", NewRunHandler, {'success': True}, name="new_run_success"),
    url(r"/new/section/(\d+)/", NewSectionHandler, name="new_section"),
    url(r"/run/(\d+)/", RunDetailsHandler, name="run_details"),
    url(r"/run/(\d+)/sections/", RunSectionsHandler, name="run_sections"),
    url(r'/static/(.*)', StaticFileHandler, {'path': STATIC_PATH}),
])

if __name__ == "__main__":
    if len(sys.argv) != 1 and len(sys.argv) != 2:
        print('''Syntax: ./start.py <port=8080>''')
        exit(1)
    
    try:
        if (len(sys.argv) == 2):
            port = int(sys.argv[1])
        else:
            port = 8080
    except ValueError, e:
        print('''ERROR: {}'''.format(e))
        print('''Syntax: ./start.py <port=8080>''')
        exit(2)
    except TypeError, e:
        print('''ERROR: {}'''.format(e))
        print('''Syntax: ./start.py <port=8080>''')
        exit(3)
    
    # Start the server
    application.listen(port)
    IOLoop.current().start()

