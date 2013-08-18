from app.site.models import SiteConfig
from .models import LyTrace
from settings import LY_TARGET, runtime_data
from yweb.orm import global_dbsession


def add_trace(hdr, ttype, tid, do, isok=True, result=None):

    '''
    hdr: RequestHandler
    ttype: target_type
    tid: target_id
    '''

    if isinstance(ttype, str):
        ttype = LY_TARGET.get(ttype, 0)

    ip = hdr.request.remote_ip
    agent = hdr.request.headers.get('User-Agent')
    visit = hdr.request.uri

    T = LyTrace(hdr.current_user, ip, agent, visit)

    T.target_type = ttype,
    T.target_id = tid,
    T.do = do
    T.isok = isok
    T.result = result

    hdr.db.add(T)
    hdr.db.commit()

    return T


def get_runtime_data(key, value=None):

    v = runtime_data.get(key)

    if v:
        return v

    db = global_dbsession()
    v = SiteConfig.get(db, key, None)
    global_dbsession.remove()

    if v:
        runtime_data[key] = v
        return v

    return value

