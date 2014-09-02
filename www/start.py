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
import uuid

WWW_PATH = path.dirname(__file__)
SCRIPT_PATH = path.join(WWW_PATH, "scripts/")
RUN_PATH = path.join(WWW_PATH, "runs/")
TEMPLATE_PATH = path.join(WWW_PATH, "templates/")
STATIC_PATH = path.join(WWW_PATH, "static/")

sys.path.append(SCRIPT_PATH)
from generate_db import DEFAULT_DB
from import_tcx import import_from_tcx

def get_template(name):
    return path.join(TEMPLATE_PATH, name+".html")

class MyRunsHandler(RequestHandler):
    def get(self):
        """ Display all the runs stored into the database
        """
        
        my_runs = list()
        conn = sqlite3.connect(DEFAULT_DB)
        with conn:
            c = conn.cursor()
            c.execute('''SELECT (julianday(start_time)-2440587.5)*86400.0,
                                time_s, distance_m, calories
                            FROM runs ORDER BY date(start_time) DESC''')
            my_runs_db = c.fetchall()
            for run in my_runs_db:
                my_runs.append({'date': run[0], 'time': run[1],
                        'distance': run[2], 'calories': run[3]})
            del my_runs_db
        self.render(get_template("my_runs"), page="my_runs", my_runs=my_runs)

class NewRunHandler(RequestHandler):
    def initialize(self, success=False):
        """ Initialize the handler
        """
        self.success = success
    
    def get(self):
        """ Display a form to add a new run into the database 
        """
        
        self.render(get_template("new_run"), page="new_run",
                success=self.success)
    
    def post(self):
        """ Add a run to the database
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
        
        self.redirect(self.reverse_url("new_run_success"))

# Define tornado application
application = Application([
    url(r"/", MyRunsHandler, name="my_runs"),
    url(r"/new/run", NewRunHandler, name="new_run"),
    url(r"/new/run/s", NewRunHandler, {'success': True}, name="new_run_success"),
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

