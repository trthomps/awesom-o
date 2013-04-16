import ConfigParser
from os.path import expanduser
from glob import glob

class Config(object):
    defaultFile = expanduser("~/.awesom-o/default.ini")
    defaultFiles = glob(expanduser("~/.awesom-o/*.ini"))

    def __init__(self, config = defaultFiles):
        self.LoadConfig(config)

    def LoadConfig(self, configFile = defaultFiles):
        self.config = ConfigParser.ConfigParser()
        if self.defaultFile == []:
            self.config.readfp(open("defaults.ini"))
            self.config.write(self.defaultFile)
        else:
            self.config.read(configFile)

    def getSection(self, section):
        if self.config.has_section(section):
            return self.config.items(section)
        else:
            return False

    def getOption(self, section, option):
        if self.config.has_section(section) and self.config.has_option(section, option):
            return self.config.get(section, option)
        else:
            return False
