import logging
from app.site.models import SiteConfig


def resource_mail_notice(hdr, user, subject=None):

    if not user:
        logging.warn('could not send notice: no user')
        return

    if not (user.email_valid and user.email and '@' in user.email):
        logging.warn('could not send notice to user(%s).' % user.id)
        return

    host = SiteConfig.get(hdr.db, 'site.host', 'http://127.0.0.1')

    if not subject:
        subject = _('[ LuoYunCloud ] Your resource has been changed')

    d = { 'return_string': True, 'USER': user,
          'account_url': host + hdr.reverse_url('account') }

    body = hdr.render('admin/user/resource_notice.html', **d)

    hdr.sendmail(subject, body, user.email)
