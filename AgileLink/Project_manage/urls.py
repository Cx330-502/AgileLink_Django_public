from django.urls import path
from .views import *

urlpatterns = [
    # path('url_name', api_name)
    # 这是一个样例，指定路由名为url_name，对应处理函数为当前app内views.py中的api_name
    path('create_project', create_project, name='create_project'),
    path('delete_project', delete_project, name='delete_project'),
    path('edit_project_info', edit_project_info, name='edit_project_info'),
    path('team_project_view', team_project_view, name='team_project_view'),
    path('recover_project', recover_project, name='recover_project'),
    path('star_project', star_project, name='star_project'),
    path('show_star_projects', show_star_projects, name='show_star_projects'),
    path('show_create_projects', show_create_projects, name='show_create_projects'),
    path('un_star_project', un_star_project, name='un_star_project'),
    path('show_single_project_info', show_single_project_info, name='show_single_project_info'),
    path('search_sort_project', search_sort_project, name='search_sort_project'),
    path('copy_project', copy_project, name='copy_project'),
]