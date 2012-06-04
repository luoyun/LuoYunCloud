from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

import settings


JOB_STATUS_STR = {
    0: _('unknown'),
    100: _('action initialized'),

    # mid-state of LY_A_NODE_RUN_INSTANCE

    200: _('running'),
    201: _('searching for node server'),
    202: _('sending request to node server'),
    210: _('waiting for resource available on node server'),
    211: _('downloading appliance image'),
    212: _('checking appliance image'),
    213: _('creating instance disk file'),
    214: _('mounting instance disk file'),
    215: _('configuring instance'),
    216: _('unmounting instance disk file'),
    221: _('starting instance virtual machine'),
    250: _('stopping instance virtual machine'),
    299: _('Last Running Status'),

    # end of mid-state of LY_A_NODE_RUN_INSTANCE

    300: _('finished'),
    301: _('finished successfully'),
    302: _('instance running already'),
    303: _('instance not running'),
    304: _('instance not exist'),
    311: _('failed'),
    321: _('node server not available'),
    322: _('node server busy'),
    331: _('appliance not available'),
    332: _('appliance error'),
    399: _('Last Finish Status'),

    # waiting for osmanager/application to start

    400: _('waiting'),
    411: _('starting OS manager'),
    412: _('syncing with OS manager'),
    421: _('checking instance status'),
    499: _('Last Waiting Status'),

    # job is pending
    500: _('pending'),

    # job is timed out
    600: _('timeout'),

    700: _('cancel'),
    701: _('Internal Error'),
    702: _('work started already'),
    703: _('node/instance busy'),
    711: _('request cancelled'),
    799: _('Last Cancel Status'),
}


JOB_ACTION_STR = {
    102: _('enable node'),
    103: _('disable node'),

    201: _('run'),
    202: _('stop'),
    206: _('destroy'),
    207: _('query'),
}



class Job(ORMBase):

    __tablename__ = 'job'

    id = Column( Integer, Sequence('job_id_seq'), primary_key=True )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User",backref=backref('jobs',order_by=id) )

    status = Column( Integer, default=settings.JOB_S_INITIATED )

    target_type = Column( Integer )
    target_id = Column( Integer )

    action = Column( Integer )

    started = Column( DateTime() )
    ended = Column( DateTime() )
    created = Column(DateTime(), default=datetime.utcnow())


    def __init__(self, user, target_type, target_id, action):
        self.user_id = user.id
        self.target_type = target_type
        self.target_id = target_id
        self.action = action

    def __repr__(self):
        return _("[Job(%s)]") % self.id

    @property
    def action_string(self):
        return JOB_ACTION_STR.get( self.action, _('Unknown') )

    @property
    def status_string(self):
        return JOB_STATUS_STR.get( self.status, _('Unknown') )
