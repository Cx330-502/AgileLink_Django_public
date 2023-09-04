from django.urls import path
from .views import *

urlpatterns = [
    # path('url_name', api_name)
    # 这是一个样例，指定路由名为url_name，对应处理函数为当前app内views.py中的api_name
    path('get_all_pages', get_all_pages),
    path('create_page', create_page),
    path('edit_page', edit_page),
    path('delete_page', delete_page),
    path('get_page_content', get_page_content),
    path('save_page_content', save_page_content),

]
