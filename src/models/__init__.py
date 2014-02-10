"""import os, sys

for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    _tmp = __import__(module[:-3], locals(), globals())
    
    for cls in [getattr(_tmp,x) for x in dir(_tmp) if isinstance(getattr(_tmp,x), type)] :
        try :
            setattr(sys.modules[__name__], cls.__name__, getattr(cls, cls.__name__))    
        except AttributeError :
            print "Warning: Unable to load class '"+cls.__name__+"' from file '"+module+"'."
del module"""

from admin import Admin
from ctype import CType
from ctask import CTask
from cresponse import CResponse
from mturkconnection import MTurkConnection
from chit import CHIT
from question import Question
from xmltask import XMLTask
