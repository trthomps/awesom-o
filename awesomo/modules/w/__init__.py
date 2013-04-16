# coding: utf-8
import re
import urllib2

class LocationUnknown(Exception):
    pass

class ParseError(Exception):
    pass

class ReadError(Exception):
    pass

def getWeather(location):
    try:
        html = urllib2.urlopen('http://thefuckingweather.com/?where=' + location).read().replace('\r','').replace('\n','')
    except:
        raise ReadError
    
    if re.search("I CAN&#39;T FIND THAT SHIT", html):
        raise LocationUnknown
       
    matched = re.match(".*<span id=\"locationDisplaySpan\" class=\"small\">(.+)</span>.*<span class=\"temperature\" tempf=\"(\d+)\">.*<p class=\"remark\">(.+)</p>.*<p class=\"flavor\">(.+)</p>.*", html)
    if matched == None:
        raise ParseError

    return matched.group(1) + ": " + matched.group(2) + "F!? " + matched.group(3) + " (" + matched.group(4) + ")"

def w(pline):
    try:
        return getWeather(pline["msg"])
    except LocationUnknown:
        return "I DON'T KNOW WHERE THE FUCK THAT IS"
    except ParseError:
        return "I CAN'T READ THE FUCKING WEATHER"
    except ReadError:
        return "I CAN'T DOWNLOAD THE FUCKING WEATHER"
