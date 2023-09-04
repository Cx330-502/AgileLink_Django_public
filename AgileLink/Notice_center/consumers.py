import json
from datetime import datetime

from Agile_models.models import *
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs

USER_DICT2 = {}


class NoticeConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        # 客户端向服务端发送websocket连接的请求时自动触发。
        # 后面三行是为了获取url中的参数
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        print(type(user))
        if user is None or user is False:
            self.accept()
            self.send(text_data=json.dumps({"errno": 1001, "errmsg": "token错误或已过期"}))
            self.close()
            raise StopConsumer()
        self.accept()
        print("1 > 客户端和通知服务端开始建立连接")
        try:
            USER_DICT2[user.id] = self
            print("1 > 客户端进入通知列表" + str(user.id))
        except Exception as e:
            print(e)
            print("1 > 客户端进入通知列表失败")

    def websocket_receive(self, message):
        pass

    def websocket_disconnect(self, message):
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        if user is None or user is False:
            self.close()
            raise StopConsumer()
        print("4 > 客户端和通知服务端断开连接")
        try:
            del USER_DICT2[user.id]
            print("4 > 客户端退出通知列表" + str(user.id))
        except Exception as e:
            print(e)
            print("4 > 客户端退出通知列表失败")
        print("5 > 客户端和通知服务端断开连接")
        self.close()
        raise StopConsumer()
