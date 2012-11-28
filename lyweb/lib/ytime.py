#!/usr/bin/env python

import time, datetime, logging
from dateutil import relativedelta


def htime( t ):

    ''' return a human ago aime '''

    if not isinstance(t, datetime.datetime):
        return 'N/A'

    ago = relativedelta.relativedelta(datetime.datetime.now(), t)

    if ago.years > 0:
        s = _('%s years ago') % ago.years

    elif ago.months > 0:
        s = _('%s months ago') % ago.months

    elif ago.days > 0:
        s = _('%s days ago') % ago.days

    elif ago.hours > 0:
        s = _('%s hours ago') % ago.hours

    elif ago.minutes > 0:
        s = _('%s minutes ago') % ago.minutes

    elif ago.seconds > 0:
        s = _('%s seconds ago') % ago.seconds

    else:
        #s = _('%s microseconds ago') % ago.microseconds
        s = _('just now')

    return s


def ftime(t, f='%Y-%m-%d %H:%M:%S'):

    try:
        return datetime.datetime.strftime(t, f)
    except Exception, e:
        #logging.error( 'format time "%s" failed: %s' % (t, e) )
        return 'N/A'
