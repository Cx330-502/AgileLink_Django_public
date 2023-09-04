from django.urls import path
from .views import *

urlpatterns = [
    # path('url_name', api_name)
    # 这是一个样例，指定路由名为url_name，对应处理函数为当前app内views.py中的api_name
    path('team_at', team_at, name='team_at'),
    path('team_at_all', team_at_all, name='team_at_all'),
    path('doc_at', doc_at, name='doc_at'),

    path('read_notice', read_notice, name='read_notice'),
    path('get_unread_notice', get_unread_notice, name='get_notice'),
    path('get_readed_notice', get_readed_notice, name='get_notice'),
    path('delete_notice', delete_notice, name='get_notice'),

    path('group_at', group_at, name='group_at'),
    path('group_at_all', group_at_all, name='group_at_all'),
]