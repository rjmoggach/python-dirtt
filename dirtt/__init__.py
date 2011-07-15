"""
python-dirtt - Directory Tree Templater
(c) 2011 Dashing Collective Inc. and contributors
Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

dirtt is a standalone tool and library used to generate 
directory and file structures from xml templates that describe 
repeatedly used filesystem layouts such as project structures
or elements therein.
"""

#v0.1.1a4
VERSION = (0, 1, 1, 'alpha', 4)

STATUSES = {'alpha': 'a', 'beta': 'b', 'releasecandidiate': 'rc' }

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    
    else:
        if VERSION[3] != 'final':
            version = '%s%s%s' % (version, STATUSES[VERSION[3]], VERSION[4])
    return version

