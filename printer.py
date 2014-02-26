# https://wiki.archlinux.org/index.php/Color_Bash_Prompt

__color = True  # overwritten by oneRun.py

def __line(f='', s=''):
    if __color:
        print '\033['+ f + s + '\033[0m'
    else:
        print s


def error(s=''):
    __line('91m', 'ERROR: '+s)


def warning(s=''):
    __line('93m','WARNING: '+s)


def msg(s=''):
    __line('30m', s)


def green(s=''):
    __line('32m', s)


def yellow(s=''):
    __line('33m', s)


def blue(s=''):
    __line('34m', s)


def purple(s=''):
    __line('35m', s)


def cyan(s=''):
    __line('36m', s)
