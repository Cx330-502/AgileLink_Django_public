import json
from datetime import datetime

from Agile_models.models import *
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs


class DocConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        # 客户端向文档服务端发送websocket连接的请求时自动触发。
        # 后面三行是为了获取url中的参数
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        doc_id = params.get("doc_id", [None])[0]
        if user is None or user is False:
            user = User.objects.get(id=1)
        if (not Documents.objects.filter(id=doc_id).exists()) or doc_id is None:
            self.accept()
            self.send(text_data=json.dumps({"errno": 1002, "errmsg": "文档不存在"}))
            self.close()
            raise StopConsumer()
        doc = Documents.objects.get(id=doc_id)
        room_name = f"d{doc_id}"
        self.accept()
        print("1 > 客户端和文档服务端开始建立连接, room_name is ", room_name)
        # 将当前连接加入到组中
        async_to_sync(self.channel_layer.group_add)(room_name, self.channel_name)
        data = []
        if Document_history.objects.filter(document=doc).count() < 1:
            self.send(text_data=json.dumps(data))
        else:
            history_list = Document_history.objects.filter(document
                                                           =doc).order_by("-edit_time").all()
            for history in history_list:
                if Team2User.objects.filter(user=history.editor,
                                            team=history.document.project.team,
                                            status__gt=0).exists():
                    nick_name = Team2User.objects.get(user=history.editor,
                                                      team=history.document.project.team).nickname
                else:
                    nick_name = history.editor.username
                if history.editor.avatar.name is None or history.editor.avatar.name == "":
                    avatar_url = None
                else:
                    avatar_url = settings.BACKEND_URL + history.editor.avatar.url
                data.append( {
                    "doc_id": doc_id,
                    "history_id": history.id,
                    "content": history.content,
                    "editor": history.editor.id,
                    "editor_name": nick_name,
                    "editor_username": history.editor.username,
                    "editor_avatar": avatar_url,
                    "edit_time": history.edit_time.strftime("%Y-%m-%d %H:%M:%S")
                })
            self.send(text_data=json.dumps(data))

    def websocket_receive(self, message):
        # 客户端基于websocket向文档服务端发送数据时，自动触发接收消息。
        print(f"2 > 文档服务端接收客户端的消息, message is {message}")
        recv_data = json.loads(message["text"])
        send_data = {"errno": 0, "errmsg": "发送成功"}
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        doc_id = params.get("doc_id", [None])[0]
        force = recv_data.get("force")
        if user is None or user is False:
            user = User.objects.get(id=1)
        if user is None or user is False or doc_id is None:
            send_data["errno"] = 1001
            send_data["errmsg"] = "token错误或已过期"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            self.close()
            raise StopConsumer()
        if (not Documents.objects.filter(id=doc_id).exists()) or doc_id is None:
            send_data["errno"] = 1002
            send_data["errmsg"] = "文档不存在"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            self.close()
            raise StopConsumer()
        doc = Documents.objects.get(id=doc_id)
        if force is None or force is False:
            send_data["errno"] = 1003
            send_data["errmsg"] = "未确定是否强制保存"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            self.close()
            raise StopConsumer()
        msg_text = recv_data.get("text")
        if (not Document_history.objects.filter(document=doc).exists()
        ) or Document_history.objects.filter(document=doc).count() < 10:
            history = Document_history(content=msg_text, document=doc, editor=user)
            history.save()
        else:
            history = Document_history.objects.filter(document=doc).order_by("edit_time")[0]
            history.content = msg_text
            if (datetime.now() - history.edit_time).seconds >= 60 or force == 1:
                history.save()
        if user.avatar.name is None or user.avatar.name == "":
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + user.avatar.url
        if Team2User.objects.filter(user=user, team=doc.project.team).exists():
            nick_name = Team2User.objects.get(user=user, team=doc.project.team).nickname
        else:
            nick_name = user.username
        document = {
            "doc_id": doc_id,
            "content": msg_text,
            "editor": user.id,
            "editor_name": nick_name,
            "editor_username": user.username,
            "editor_avatar": avatar_url,
            "edit_time": history.edit_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        document = json.dumps(document)
        room_name = f"d{doc_id}"
        doc.project.edit_time = datetime.now()
        doc.project.editor = user
        async_to_sync(self.channel_layer.group_send)(room_name, {
            "type": "doc.message",
            "message": document,
        })

    def doc_message(self, event):
        # 接收到消息后，自动触发向客户端发送消息。
        print(f"3 > 文档服务端向客户端发送消息, event is {event}")
        self.send(text_data=event["message"])

    def websocket_disconnect(self, message):
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        if user is None or user is False:
            user = User.objects.get(id=1)
        doc_id = params.get("doc_id", [None])[0]
        if (not Documents.objects.filter(id=doc_id).exists()) or doc_id is None:
            self.close()
            raise StopConsumer()
        async_to_sync(self.channel_layer.group_discard)(f"d{doc_id}", self.channel_name)
