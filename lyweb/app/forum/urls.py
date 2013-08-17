from tornado.web import url
from . import views as forum
from . import admin_views as admin

handlers = [
    url( r'/forum', forum.Index, name="forum" ),

    url( r'/forum/catalog', forum.CatalogIndex,
         name="forum:catalog" ),

    # topic
    url( r'/forum/topic/add', forum.TopicAdd,
         name="forum:topic:add" ),

    url( r'/forum/topic/view', forum.TopicView,
         name="forum:topic:view" ),

    url( r'/forum/topic/edit', forum.TopicEdit,
         name="forum:topic:edit" ),

    url( r'/forum/topic/reply', forum.TopicReply,
         name="forum:topic:reply" ),

    url( r'/forum/topic/delete', forum.TopicDelete,
         name="forum:topic:delete" ),

    url( r'/forum/topic/vote', forum.TopicVote,
         name="forum:topic:vote" ),

    # post
    url( r'/forum/post/reply', forum.PostReply,
         name="forum:post:reply" ),

    url( r'/forum/post/edit', forum.PostEdit,
         name="forum:post:edit" ),

    url( r'/forum/post/vote', forum.PostVote,
         name="forum:post:vote" ),

    # tag
    url( r'/forum/tag', forum.TagHome, name="forum:tag:home" ),
    url( r'/forum/tag/view', forum.TagView, name="forum:tag:view" ),


    # admin
    url( r'/admin/forum', admin.Index, name="admin:forum"),

    url( r'/admin/forum/catalog', admin.CatalogIndex,
         name="admin:forum:catalog"),

    url( r'/admin/forum/catalog/view', admin.CatalogView,
         name="admin:forum:catalog:view"),

    url( r'/admin/forum/catalog/add', admin.CatalogAdd,
         name="admin:forum:catalog:add"),

    url( r'/admin/forum/catalog/edit', admin.CatalogEdit,
         name="admin:forum:catalog:edit"),
]
