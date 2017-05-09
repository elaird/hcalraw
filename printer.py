# https://wiki.archlinux.org/index.php/Color_Bash_Prompt
# http://misc.flogisoft.com/bash/tip_colors_and_formatting

__color = True  # overwritten by oneRun.py

def __line(f, s, p):
    if __color:
        s = '\033['+ f + s + '\033[0m'

    if p:
        print s
    return s


def error(s=''):
    return red('ERROR: ' + s)

def warning(s=''):
    return red('WARNING: ' + s)

def info(s=''):
    return cyan('INFO: ' + s)


def msg(s='', p=True):
    return __line('0m', s, p)

def bold(s='', p=True):
    return __line('1m', s, p)

def underline(s='', p=True):
    return __line('4m', s, p)

def green(s='', p=True):
    return __line('32m', s, p)

def yellow(s='', p=True):
    return __line('33m', s, p)

def dark_blue(s='', p=True):
    return __line('34m', s, p)

def purple(s='', p=True):
    return __line('35m', s, p)

def cyan(s='', p=True):
    return __line('36m', s, p)

def gray(s, p=True):
    return __line('90m', s, p)

def red(s, p=True):
    return __line('91m', s, p)

def blue(s='', p=True):
    return __line('94m', s, p)
