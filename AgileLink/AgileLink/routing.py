from django.urls import re_path, path

import Public_chat.consumers as chat_consumers
import Doc_edit.consumers as doc_consumers
import Notice_center.consumers as notice_consumers

websocket_urlpatterns = [
    # re_path(r'^ws/chat/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    path('api/v1/ws/chat/', chat_consumers.ChatConsumer.as_asgi()),
    path('api/v1/ws/doc/', doc_consumers.DocConsumer.as_asgi()),
    path('api/v1/ws/notice/',notice_consumers.NoticeConsumer.as_asgi())
]
