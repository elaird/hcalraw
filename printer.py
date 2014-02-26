__color = True  # overwritten by oneRun.py


def msg(s="", n=0):
    if __color:
        print ('\033[%dm' % n) + s + '\033[0m'
    else:
        print s

def warning(s=""):
    msg("WARNING: "+s, 93)

def error(s=""):
    msg("ERROR: "+s, 91)

def info(s=""):
    msg("INFO: "+s, 94)
        
def more(s=""):
    msg(s, 94)

def less(s=""):
    msg(s, 92)


