import os

# This will import all modules
for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] == "pyc":
        continue
    if module[:-3] == ".py":
        __import__(module[:-3], locals(), globals())
    else:
        __import__(module, locals(), globals())
del module
del os
