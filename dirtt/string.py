import re

def rand():
    """generate an 8 random character name for tempfiles
    """
    chars = string.letters + string.digits
    rnd = ''
    for i in range(8):
        rnd = rnd + choice(chars)
    return rnd


def clean(bad_text):
    """sanitizes a string to our preference
    """
    ## convert the text
    #wash = string.lower(bad_text).strip()
    wash = string.strip(bad_text)
    # change - & " " to _
    #soap = re.sub('([\ -])','_',wash)
    soap = re.sub('([\ ])','_',wash)
    # strip out strange characters
    rinse = re.sub('[^A-za-z0-9-_\.<>%]','',soap)
    # squeeze repeating underscores
    spin = re.sub('[_]+','_',rinse)
    return spin


def byte_size(bytes):
    """Convert bytes to KB, MB, GB, or TB depending
       on how long the number is"""
    if bytes < 1024:
        converted = bytes
        unit = 'Bytes'
    elif bytes < 2**20:
        converted = "%.2f" % (bytes/float(2**10))
        unit = 'KB'
    elif bytes < 2**30:
        converted = "%.2f" % (bytes/float(2**20))
        unit = 'MB'
    elif bytes < 2**40:
        converted = "%.2f" % (bytes/float(2**30))
        unit = 'GB'
    elif bytes < 2**50:
        converted = "%.2f" % (bytes/float(2**40))
        unit = 'TB'
    else:
        converted = "%.2f" % (bytes/float(2**50))
        unit = 'PB'
    return converted,unit
