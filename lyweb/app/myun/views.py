# coding: utf-8

import json, logging
from datetime import datetime
from lycustom import RequestHandler

from app.auth.models import User
from app.instance.models import Instance
from app.appliance.models import Appliance, ApplianceCatalog
from app.job.models import Job
from app.system.models import LuoYunConfig
from app.network.models import IPPool

from settings import JOB_TARGET

import tornado
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_

from lytool.filesize import size as human_size
from ytool.pagination import pagination


from settings import INSTANCE_DELETED_STATUS as DELETED_S

import settings


class Index(RequestHandler):

    @authenticated
    def get(self):

        my = self.db.query(User).get(self.current_user.id)

        d = { 'my': my, 'human_size': human_size }

        d['title'] = self.trans(_('My LuoYun'))

        self.render("myun/index.html", **d)
