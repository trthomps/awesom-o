import socket
import json
import time
import re
import threading
import Queue
import sys
from pprint import pprint as pp
from awesomo import config

class ircbot(object):
    def __init__(self,config):
        self.config = config

    def send(self,message):
        print "[>>>]" + message
        self.sock.send(message + "\r\n")

    def say(self,to,message):
        self.send("PRIVMSG " + to + " :" + message)

    def parse_line(self,line):
        ret = { "nick": "", "user": "", "host": "", "code": "", "cmd": "", "target": "", "msg": "" }

        if line[0] == ":":
            # :test!test@yakko.cs.wmich.edu MODE test :+i
            # :butters!trthomps@141.218.143.78 PRIVMSG #test :testing
            # :butters!trthomps@141.218.143.78 TOPIC #test :foo | bar
            matched = re.match("^:([\w_-]+)!([\w_-]+)@([\w\._-]+) (\w+) ([\w#_-]+) :(.+)$", line)
            if matched != None:
                ret["nick"] = matched.group(1)
                ret["user"] = matched.group(2)
                ret["host"] = matched.group(3)
                ret["cmd"] = matched.group(4)
                ret["target"] = matched.group(5)
                ret["msg"] = matched.group(6)

                return ret
            
            # :dot.cs.wmich.edu 001 test :Welcome to the CClub Internet Relay Chat Network test
            # :dot.cs.wmich.edu 376 test :End of /MOTD command.
            # :dot.cs.wmich.edu NOTICE test :*** Spoofing your IP. congrats.
            matched = re.match("^:([\w\.-]+) (\d+|\w+) ([\w#_-]+) :(.+)$", line)
            if matched != None:
                ret["host"] = matched.group(1)
                ret["code"] = matched.group(2)
                ret["cmd"] = matched.group(2)
                ret["target"] = matched.group(3)
                ret["msg"] = matched.group(4)

                return ret

            # :dot.cs.wmich.edu 366 test #test :End of /NAMES list.
            # :dot.cs.wmich.edu 433 * butters :Nickname is already in use.
            matched = re.match("^:([\w\.-]+) (\d+) ([\w_-]+|\*) ([a-zA-Z0-9#_-]+) :(.+)$", line)
            if matched != None:
                ret["host"] = matched.group(1)
                ret["code"] = matched.group(2)
                ret["nick"] = matched.group(3)
                ret["target"] = matched.group(4)
                ret["msg"] = matched.group(5)

                return ret

        else:
            splitline = line.split()
            ret["cmd"] = splitline[0]
            if splitline[0] == "PING":
                if len(splitline) == 2:
                    if splitline[1][0] == ":":
                        splitline[1] = splitline[1][1:]
                    ret["host"] = splitline[1]
                elif len(splitline) == 3:
                    ret["user"] = splitline[1]
                    ret["host"] = splitline[2]

                return ret

        print "[<E<]" + line
        return ret

    def print_pline(self,ret):
        print "[<P<]nick: " + ret["nick"] + " | user: " + ret["user"] + " | host: " + ret["host"] + " | code: " + ret["code"] + " | cmd: " + ret["cmd"] + " | target: " + ret["target"] + " | msg: " + ret["msg"]

    def handle_line(self):
        while True:
            rawline = self.lineHandlerQueue.get()
            self.threadsAvailable -= 1
            #print "[<H<]" + rawline
            pline = self.parse_line(rawline)
            #self.print_pline(pline)

            if pline["code"] != "":
                if pline["code"] == "376":
                    for channel in json.loads(self.config.getOption("irc","channels")):
                        self.send("JOIN " + channel)

            if pline["cmd"] != "":
                if pline["cmd"] == "PRIVMSG":
                    if pline["msg"] == "!test":
                        self.say(pline["target"],"I am the awesom-o bot 4000 running on Python " + str(sys.version.split()[0]) + ". I have " + str(self.threadsAvailable) + "/" + str(self.config.getOption("irc","threads")) + " available not counting this one.")
                        time.sleep(5)
                if pline["cmd"] == "PING":
                    self.send("PONG " + pline["host"])

            self.threadsAvailable += 1
            self.lineHandlerQueue.task_done()


    def run(self):
        self.joined = False

        # Create IRC Socket
        self.sock = socket.socket()
        self.sock.connect( (self.config.getOption("irc","host"), int(self.config.getOption("irc","port"))) )

        # Send IDENT info
        self.send("NICK " + self.config.getOption("irc","nick"))
        self.send("USER " + self.config.getOption("irc","username") + " " + self.config.getOption("irc","host") + " 8 : Butters' very own robot!")
        
        # Create thread pool for handling incoming 
        self.lineHandlerQueue = Queue.Queue()
        self.threadsAvailable = int(self.config.getOption("irc","threads"))
        for i in range(int(self.config.getOption("irc","threads"))):
            t = threading.Thread(target=self.handle_line)
            t.daemon = True
            t.start()

        # Loop
        while True:
            # Read line
            rawlines = self.sock.recv(4096).strip("\r").split('\n')

            # Handle each line
            for rawline in rawlines:
                rawline = rawline.strip()
                if rawline != "":
                    print "[<<<]" + rawline
                    # Send line to thread pool
                    self.lineHandlerQueue.put(rawline)

        self.sock.close()
