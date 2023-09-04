from django.urls import path
from .views import *

urlpatterns = [
    # path('url_name', api_name)
    # 这是一个样例，指定路由名为url_name，对应处理函数为当前app内views.py中的api_name
    path('login_get_messages', login_get_messages),
    path('get_new_messages', get_new_messages),
    path('exit_chat', exit_chat),
    path('search_message', search_message),

    path('get_message', get_message),

    path('group/create_group', create_group),
    path('group/edit_group', edit_group),
    path('group/get_group_list', get_group_list),
    path('group/invite_member', invite_member),
    path('group/exit_group', exit_group),
    path('group/get_group_member_list', get_group_member_list),
    path('group/dismiss_group', dismiss_group),
]