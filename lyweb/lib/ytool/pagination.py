import re, urlparse, urllib
from mako.template import Template

PAGE_TEMPLATE = '''<div class="pagination">
<ul>
  % if cur_page > 1:
  <li><a href="${ page_url(cur_page -1) }">${ _("Prev") }</a></li>
  % else:
  <li class="disabled"><span>${ _("Prev") }</span></li>
  % endif

  % for p in plist:
  % if p == cur_page:
  <li class="active"><span>${ p }</span></li>
  % elif p == notexist_page:
  <li><span>...</span></li>
  % else:
  <li><a href="${ page_url(p) }">${ p }</a></li>
  % endif
  % endfor

  % if cur_page < page_sum:
  <li><a href="${ page_url(cur_page + 1) }">${ _("Next") }</a></li>
  % else:
  <li class="disabled"><span>${ _("Next") }</span></li>
  % endif
</ul>


  % if sepa_range:
<ul>
    %for s in sepa_range:
    %if sepa == s:
    <li class="active"><span>${ s }</span></li>
    % else:
    <li><a href="${ psize_url(s) }">${ s }</a></li>
    % endif
    %endfor
</ul>
  % endif
</div>'''


def pagination( url, total, sepa, cur, list_size=5,
                sepa_range=[] ):

    if total <= sepa:
        return ''

    sepa_range = [x for x in sepa_range if x < total]

    page_sum = total / sepa
    if ( total % sepa ): page_sum += 1

    notexist_p = page_sum + 1


    last_p = page_sum
    start = ( cur / (list_size + 1) ) * list_size + 1
    end = start + list_size
    if end > last_p: end = last_p

    plist = range(start, end + 1)

    if end < last_p:
        plist.extend( [notexist_p, last_p] )

    if cur > list_size:
        plist.insert(0, notexist_p)
        plist.insert(0, 1)

    def _page_url(cur):
        return page_url(url, cur)

    d = { 'total': total, 'plist': plist,  'sepa': sepa,
          'cur_page': cur, 'page_sum': page_sum,
          'notexist_page': notexist_p,
          'page_url': _page_url }

    if sepa_range:
        def _psize_url(cur):
            return psize_url(url, cur)
        d['psize_url'] = _psize_url
        d['sepa_range'] = sepa_range

    t = Template( PAGE_TEMPLATE )
    return t.render(**d)


def page_url(uri, cur):

    if '?' not in uri:
        return uri + '?p=%s' % cur

    path, params = uri.split('?')
    new = []
    find_p = False
    for k, v in urlparse.parse_qsl( params ):
        if k == 'p':
            v = cur
            find_p = True
        new.append( (k, v) )

    if not find_p:
        new.append( ('p', cur) )

    return '?'.join([path, urllib.urlencode(new)])


def psize_url(uri, cur):

    if '?' not in uri:
        return uri + '?sepa=%s' % cur

    path, params = uri.split('?')
    new = []
    find_sepa = False
    for k, v in urlparse.parse_qsl( params ):
        if k == 'sepa':
            v = cur
            find_sepa = True
        if k == 'p':
            v = 1
        new.append( (k, v) )

    if not find_sepa:
        new.append( ('sepa', cur) )

    return '?'.join([path, urllib.urlencode(new)])

