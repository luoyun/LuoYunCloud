import re
import datetime
import ConfigParser
import logging

from yweb.orm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

from sqlalchemy import and_


class Resource(ORMBase):

    ''' LuoYunCloud resource management '''

    T_CPU      = 1
    T_MEMORY   = 2
    T_STORAGE  = 3
    T_INSTANCE = 4

    RESOURCE_TYPE = [
        (T_CPU,      _('CPU')),
        (T_MEMORY,   _('Memory')),
        (T_STORAGE,  _('Storage')),
        (T_INSTANCE, _('Instance')) ]

    __tablename__ = 'resource'

    id = Column(Integer, Sequence('resource_id_seq'), primary_key=True)

    user_id = Column( Integer, ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('resources', order_by=id) )

    type = Column( Integer ) # RESOURCE_TYPE

    ## resource size
    # CPU        number
    # Memory     M
    # Storage    M
    # Instance   number
    size = Column( Integer )

    created = Column(DateTime(), default=datetime.datetime.now)
    updated = Column(DateTime(), default=datetime.datetime.now)

    effect_date  = Column(DateTime(), default=datetime.datetime.now)
    expired_date = Column(DateTime())


    def __init__(self, user, rtype, size, effect_date=None, expired_date=None):
        self.user_id = user.id
        self.type = rtype
        self.size = size

        if effect_date:
            self.effect_date = effect_date

        if expired_date:
            self.expired_date = expired_date
        else:
            self._set_default_expired_date()


    def __str__(self):
        return 'Resource <%s>' % self.id

    @property
    def type_str(self):
        for x, y in self.RESOURCE_TYPE:
            if x == self.type:
                return y

        return _('Unknown')

    @property
    def size_str(self):

        if self.type == self.T_CPU:
            return _('%s core') % self.size

        elif self.type == self.T_MEMORY:
            return _('%s M') % self.size

        elif self.type == self.T_STORAGE:
            return _('%s G') % self.size

        elif self.type == self.T_INSTANCE:
            return _('%s') % self.size

        else:
            return _('Unknown unit for size %s') % self.size

    @property
    def contextual_class(self):
        # TODO: referrence bootstrap
        now = datetime.datetime.now()

        c = ''

        if now < self.effect_date:
            c = 'warning'

        elif self.effect_date < now < self.expired_date:
            # does not needed
            #c = 'success'
            pass

        elif self.expired_date < now:
            c = 'error'

        return c


    @staticmethod
    def get_type_select(clc):
        # TODO
        return clc.RESOURCE_TYPE


    def _set_default_expired_date(self):

        indate = None
        units = 'seconds'

        cf = ConfigParser.ConfigParser().read( settings.sitecfg )

        if cf.has_option('resource', 'default_indate'):

            indate = cf.get('resource', 'default_indate')

            try:
                indate = int(indate)
            except ValueError, e:
                r = re.compile("([0-9]+)[ \t]*([a-zA-Z]+)")
                m = r.match(indate)
                if m and len(m.groups) == 2:

                    indate = int( m.group(1) )

                    t = m.groups(2).lower().strip()

                    if t in ['seconds', 's', 'minutes', 'm',
                             'hours', 'h', 'days', 'd' ]:
                        units = t
                    else:
                        logging.error('unknown units for default_indate value: "%s"' % t)

        if not indate:
            indate = 24 * 3600 # 1 days

        if units in ['minutes', 'm']:
            indate = indate * 60
        elif units in ['hours', 'h']:
            indate = indate * 3600
        elif units in ['days', 'd']:
            indate = indate * 3600 * 24

        self.expired_date =  datetime.datetime.now() + \
            datetime.timedelta( seconds = indate )

