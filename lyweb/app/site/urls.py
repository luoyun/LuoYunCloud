from tornado.web import url
from . import admin_views

handlers = [

    url( r'/admin/site',
         admin_views.Index, name="admin:site" ),

    # nav
    url( r'/admin/site/nav',
         admin_views.NavIndex, name="admin:site:nav" ),

    url( r'/admin/site/nav/add',
         admin_views.NavAdd, name="admin:site:nav:add" ),

    url( r'/admin/site/nav/([0-9]+)/edit',
         admin_views.NavEdit, name="admin:site:nav:edit" ),

    url( r'/admin/site/nav/delete',
         admin_views.ajaxNavDelete, name="admin:site:nav:ajax_delete" ),

    url( r'/admin/site/nav/position_adjust',
         admin_views.ajaxNavPositionAdjust, name="admin:site:nav:ajax_position_adjust" ),

    # entry
    url( r'/admin/site/entry', admin_views.EntryIndex, name="admin:site:entry" ),

    url( r'/admin/site/entry/add',
         admin_views.EntryAdd, name="admin:site:entry:add" ),

    url( r'/admin/site/entry/([0-9]+)/edit',
         admin_views.EntryEdit, name="admin:site:entry:edit" ),

    url( r'/admin/site/entry/delete',
         admin_views.ajaxEntryDelete, name="admin:site:entry:ajax_delete" ),


    # article
    url( r'/admin/site/article', admin_views.ArticleIndex, name="admin:site:article" ),

    url( r'/admin/site/article/add',
         admin_views.ArticleAdd, name="admin:site:article:add" ),

    url( r'/admin/site/article/([0-9]+)/edit',
         admin_views.ArticleEdit, name="admin:site:article:edit" ),

    url( r'/admin/site/article/delete',
         admin_views.ajaxArticleDelete, name="admin:site:article:ajax_delete" ),

]
