from django.urls import path
from .views import *

urlpatterns = [
    # path('url_name', api_name)
    # 这是一个样例，指定路由名为url_name，对应处理函数为当前app内views.py中的api_name
    path('user/captcha',captcha,name='captcha'),
    path('user/register', user_register),
    path('user/login', user_login),
    path('user/upload_avatar', upload_avatar),
    path('user/get_avatar', get_avatar),
    path('user/change_info', change_info),
    path('user/change_password', change_password),
    path('user/change_email', change_email),
    path('file_receive', file_receive, name='file_receive'),
    path('create_team', create_team),

    path('generate_team_link', generate_team_link, name='generate_team_link'),
    path('invite_member', invite_member, name='invite_member'),
    path('invitee_handle_invitation', invitee_handle_invitation, name='invitee_handle_invitation'),
    path('apply_join_team', apply_join_team, name='apply_join_team'),
    path('applicant_handle_application', applicant_handle_application, name='applicant_handle_application'),

    path('delete_member', delete_member, name='delete_member'),
    path('grant_admin', grant_admin, name='grant_admin'),
    path('dismiss_admin', dismiss_admin, name='dismiss_admin'),

    path('view_member_info', view_member_info, name='view_member_info'),
    path('view_team_info', view_team_info, name='view_team_info'),
    path('edit_personal_info', edit_personal_info, name='edit_personal_info'),
    path('show_single_team_info', show_single_team_info, name='show_single_team_info'),

    path('user/get_user_info', get_user_info, name='get_member_list'),
]
