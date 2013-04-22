import re
import sys
import sqlite3
import os
from datetime import datetime

def quote(pline):
    try:
        cmd,pline["msg"] = pline["msg"].split(None,1)
    except ValueError:
        cmd = pline["msg"]
        pline["msg"] = ""

    if cmd in CMDS:
        return eval(MODNAME + "_" + cmd + "(" + str(pline) + ")")
    else:
        return usage()

def quote_add(pline):
    QDB_CONN = sqlite3.connect('%s/quotedb.sqlite' % os.path.dirname(__file__))
    QDB = QDB_CONN.cursor()
    
    if re.match("^usage",pline["msg"]) or pline["msg"] == "":
        return usage("add", "[quote]: Adds a quote to the quote database.")

    # Create the table if it doesn't already exist
    QDB.execute('''CREATE TABLE IF NOT EXISTS "quotedb" ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "quote" VARCHAR NOT NULL , "set_by" VARCHAR NOT NULL , "set_time" DATETIME NOT NULL )''')

    QDB.execute('''INSERT INTO "main"."quotedb" ("quote","set_by","set_time") VALUES (?, ?, ?)''', (pline["msg"], pline["nick"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")) )
    QDB_CONN.commit()
    
    return "Quote #%d added!" % QDB.lastrowid

def quote_get(pline):
    QDB_CONN = sqlite3.connect('%s/quotedb.sqlite' % os.path.dirname(__file__))
    QDB = QDB_CONN.cursor()
    
    if re.match("^usage",pline["msg"]) or pline["msg"] == "":
        return usage("get", "[quote id]: Returns a quote by id.")

    QDB.execute("SELECT * FROM \"main\".\"quotedb\" WHERE id =:id LIMIT 1", {"id": pline["msg"]})

    return quoteToString(QDB.fetchone())

def quote_random(pline):
    QDB_CONN = sqlite3.connect('%s/quotedb.sqlite' % os.path.dirname(__file__))
    QDB = QDB_CONN.cursor()
    
    if re.match("^usage",pline["msg"]):
        return usage("random", "[set by]: Returns a random quote set by [set by] if specified.")

    if pline["msg"] == "":
        QDB.execute("SELECT * FROM \"main\".\"quotedb\" ORDER BY RANDOM() LIMIT 1")
    else:
        QDB.execute("SELECT * FROM \"main\".\"quotedb\" WHERE quote LIKE ? ORDER BY RANDOM() LIMIT 1", ("%%%s%%" % pline["msg"],))

    return quoteToString(QDB.fetchone())

def quote_search(pline):
    QDB_CONN = sqlite3.connect('%s/quotedb.sqlite' % os.path.dirname(__file__))
    QDB = QDB_CONN.cursor()
    
    if re.match("^usage",pline["msg"]) or pline["msg"] == "":
        return usage("search","[string]: Returns a list of quote ids with [string].")

    QDB.execute("SELECT id FROM \"main\".\"quotedb\" WHERE quote LIKE ?", ("%%%s%%" % pline["msg"],))
    results = QDB.fetchall()
    ids = [ str(result[0]) for result in results ]

    if len(ids):
        return "%s Quotes Found: %s" % (str(len(ids)), ", ".join(ids))
    else:
        return "No Quotes Found!"

def usage(cmd = None, msg = None):
    if not cmd:
        cmd = "[%s]" % "|".join(CMDS)
        msg = "Say !%s [cmd] usage for more details." % MODNAME
        
    return "!%s %s %s" % (MODNAME, cmd, msg)

def quoteToString(quote):
    try:
        return "Quote #%d: \"%s\" set by %s on %s" % quote
    except TypeError:
        return "No Quotes Found!"

try:
    MODNAME = __name__.rsplit('.', 1)[1]
except ValueError:
    MODNAME = __name__
CMDS = [ obj.split("_")[1] for obj in dir(sys.modules[__name__]) if re.match("^" + MODNAME + "_",obj) ]
