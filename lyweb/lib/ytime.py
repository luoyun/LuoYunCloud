#!/usr/bin/env python

import time

def ytime_human(dt):

    '''return time string for human
    '''
    now = time.localtime()
    dt = str(dt).split('.')[0]
    dt = str(dt).split('+')[0]

    try:
        old = time.strptime(dt, '%Y-%m-%d %H:%M:%S')
    except:
        return ''

    interval = (now.tm_year - old.tm_year) * 365 + (now.tm_yday - old.tm_yday)

    if interval < 1:
        if now.tm_hour > old.tm_hour:
            if now.tm_min > old.tm_min:
                humantime = _('%s hours') % (now.tm_hour - old.tm_hour)
            else:
                humantime = _('%s minutes') % (now.tm_min + 60 - old.tm_min)
        else:
            humantime = _('%s seconds') % (now.tm_sec - old.tm_sec)
    elif interval == 1:
        humantime = _('yestoday')
    elif interval < 30:
        humantime = _('%s days') % interval
    elif interval < 365:
        humantime = _('%s months') % (interval / 30)
    else:
        humantime = _('%s years') % (interval / 365)

    return humantime
