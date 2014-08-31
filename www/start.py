#!/usr/bin/python

# Launch a very light-HTTP server: Tornado
#
# Requirements (import from):
#   -  tornado
#
# Syntax:
#   ./start.py <port=8080>

import tornado.ioloop
import tornado.web

import sys
from os import path

WWW_DIRECTORY = path.dirname(__file__)
sys.path.append(path.join(WWW_DIRECTORY, "../scripts/"))
from generate_db import DEFAULT_DB

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World ^^")

# Define tornado application
application = tornado.web.Application([
    (r"/", MainHandler),
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
    tornado.ioloop.IOLoop.instance().start()

