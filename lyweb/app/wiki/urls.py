from tornado.web import url
import app.wiki.views as wiki

handlers = [

    url(r'/wiki', wiki.Index, name='wiki:index'),
    url(r'/wiki/topic/([0-9]+)', wiki.ViewTopic, name='wiki:view'),
    url(r'/wiki/topic/([0-9]+)/edit', wiki.EditTopic, name='wiki:edit'),
    url(r'/wiki/topic/([0-9]+)/delete', wiki.DeleteTopic, name='wiki:delete'),
    url(r'/wiki/topic/add', wiki.NewTopic, name='wiki:add'),
    url(r'/wiki/catalog/([0-9]+)', wiki.ViewCatalog, name='wiki:view_catalog'),

    (r'/wiki/topic/([0-9]+)/source', wiki.ViewTopicSource),

]
