from django.urls import path
from .views import *

urlpatterns = [
    # path('url_name', api_name)
    # 这是一个样例，指定路由名为url_name，对应处理函数为当前app内views.py中的api_name
    path('create_doc/', create_doc),
    path('rename_doc/', rename_doc),
    path('delete_doc/', delete_doc),
    path('get_doc_list/', get_doc_list),
    path('get_readonly_link/', get_readonly_link),
    path('get_edit_link/', get_edit_link),
    path('export_doc/', export_doc),
    path('create_dictionary/', create_dictionary),
    path('delete_dictionary/', delete_dictionary),
    path('move_doc/', move_doc),
    path('rename_dictionary/', rename_dictionary),
    path('show_file_tree/', show_file_tree),
]
