# coding: utf-8
import socket
import json
import time
import re
import threading
import Queue
import sys
import string
import urllib2
from awesomo import config
from awesomo import modules

class ircbot(object):
    def __init__(self,config):
        self.config = config
        
        self.nick = self.config.getOption("irc","nick")
        self.username = self.config.getOption("irc","username")
        self.host = self.config.getOption("irc","host")

    def send(self,message):
        print "[>>>]%s" % message
        self.sock.send("%s\r\n" % message)

    def say(self,to,message):
        i = 0
        while True:
            j = 450
            
            if(len(message[i:i+j+1]) > j):
                while message[i:i+j][-1:] != " ":
                    j -= 1
                
            if message[i+j:i+j+450] != "":
                toSend = "%s..." % message[i:i+j-1]
            else:
                toSend = message[i:i+j]
            
            self.send("PRIVMSG %s :%s" % (to, toSend))
            
            i += j
            if message[i:i+j] == "":
                break

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

        print "[<E<]%s" % line
        return ret

    def handle_line(self):
        while True:
            rawline = self.lineHandlerQueue.get()
            self.threadsAvailable -= 1
            pline = self.parse_line(rawline)

            if pline["code"]:
            
                if pline["code"] == "376":
                    for channel in json.loads(self.config.getOption("irc","channels")):
                        self.send("JOIN %s" % channel)
                
                if pline["code"] == "433":
                    self.nick = "%s_" % self.nick
                    self.send("NICK %s" % self.nick)

            elif pline["cmd"]:
            
                if pline["cmd"] == "PRIVMSG":
                    if pline["target"][:1] == "#":
                        sendTo = pline["target"]
                    else:
                        sendTo = pline["nick"]
                
                    if pline["msg"][0] == "!":
                        try:
                            module,pline["msg"] = pline["msg"].split(' ', 1)
                        except ValueError:
                            module = pline["msg"]
                            pline["msg"] = ""
                        finally:
                            module = module[1:]
                        
                        if module in dir(modules):
                            print "[MOD] Running module " + module + "(" + str(pline) + ")"
                            self.say(sendTo,eval("modules." + module + "." + module + "(" + str(pline) + ")"))
                            
                    TLDS = [ string.lower(line.strip()) for line in urllib2.urlopen('http://data.iana.org/TLD/tlds-alpha-by-domain.txt') if line[:1] != "#"  if line[:2] != "XN" ]
                    urlMatched = re.match(r'(?:^|.* )((?:https?://)?[a-zA-Z0-9.-]+\.(?:%s){1}\S*)(?:$| .*)' % "|".join(TLDS), pline["msg"])
                    if urlMatched:
                        try:
                            html = urllib2.urlopen(urlMatched.group(1)).read().replace('\r','').replace('\n','')
                        except:
                            return
                        titleMatched = re.match('.*<title>(.*)</title>.*',html)
                        if titleMatched:
                            if len(urlMatched.group(1) > 50):
                                shortURL = "" # This will be our bit.ly shorten place
                            else:
                                shortURL = ""
                            self.say(sendTo,"%s%s" % (shortURL, titleMatched.group(1)))

                if pline["cmd"] == "PING":
                    self.send("PONG " + pline["host"])

            self.threadsAvailable += 1
            self.lineHandlerQueue.task_done()


    def run(self):
        # Create IRC Socket
        self.sock = socket.socket()
        self.sock.connect( (self.config.getOption("irc","host"), int(self.config.getOption("irc","port"))) )

        # Send IDENT info
        self.send("NICK %s" % self.nick )
        self.send("USER %s %s 8 : Butters' very own robot!" % (self.username, self.host))
        
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
