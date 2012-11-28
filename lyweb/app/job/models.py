from datetime import datetime
from lyorm import ORMBase

from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

import settings

from lyorm import dbsession as db
from app.node.models import Node
from app.instance.models import Instance
from app.account.models import User

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
    259: _('virtual machine stopped'),
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
    323: _('original node server is not enable'),
    331: _('appliance download error'),
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
    104: _('update node configure'),
    201: _('run'),
    202: _('stop'),
    206: _('destroy'),
    207: _('query'),
}


JOB_TARGET_NAME = {
    3: _('NODE'),
    4: _('INSTANCE'),
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
    created = Column(DateTime(), default=datetime.now)


    def __init__(self, user, target_type, target_id, action):
        self.user_id = user.id
        self.target_type = target_type
        self.target_id = target_id
        self.action = action

    def __repr__(self):
        return _("[Job(%s)]") % self.id

    @property
    def target_name(self):
        # TODO: merge with settings.JOB_TARGET
        return JOB_TARGET_NAME.get(self.target_type, _('Unknown'))

    @property
    def target_url(self):
        # TODO: use reverse_url
        url = ''
        try:
            if ( self.target_type == 3 and
                 db.query(Node).get(self.target_id) ):
                url = '/admin/node?id=%s&action=view' % self.target_id
            elif ( self.target_type == 4 and
                   db.query(Instance).get(self.target_id) ):
                url = '/admin/instance?id=%s' % self.target_id
        except:
            pass

        if url:
            return '<a href="%s" target="_blank">%s</a>' % (url, self.target_id)
        else:
            return self.target_id


    @property
    def action_string(self):
        return JOB_ACTION_STR.get( self.action, _('Unknown') )

    @property
    def status_string(self):
        return JOB_STATUS_STR.get( self.status, _('Unknown') )


    @property
    def completed(self):
        return 300 <= self.status < 400 or self.status >= 600

    @property
    def canstop(self):
        return self.status >= 300

    @property
    def waiting(self):
        return 400 <= self.status < 500

    @property
    def user_link_module(self):
        if (self.user_id and db.query(User).get(self.user_id)):
            url = '/admin/user?id=%s' % self.user_id
            return '<a href="%s" target="_blank">%s</a>' % (url, self.user.username)
