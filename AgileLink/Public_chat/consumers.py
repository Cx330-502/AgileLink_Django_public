import ast
import json

from django.core.files import File
from django.core.files.base import ContentFile

from Agile_models.models import *
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs

USER_DICT = {}


def recu_message(message, user, num):
    if message.file_content.name is None or message.file_content.name == "":
        url = ""
    else:
        url = settings.BACKEND_URL + message.file_content.url
    if message.sender.avatar.name is None or message.sender.avatar.name == "":
        avatar_url = None
    else:
        avatar_url = settings.BACKEND_URL + message.sender.avatar.url
    data = {
        'id': message.id,
        'type': message.type,
        'sender_id': message.sender.id,
        'sender_name': message.sender.username,
        'sender_username': message.sender.username,
        'sender_avatar': avatar_url,
        'receive_team_id': None,
        'receive_team_name': None,
        'receive_user_id': None,
        'receive_user_name': None,
        'receive_user_avatar': None,
        'receive_group_id': None,
        'receive_group_name': None,
        'content': message.content,
        'file_content': url,
        'message_source': [],
        'time': message.send_time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if message.type == 1:
        data['receive_team_id'] = message.receive_team.id
        data['receive_team_name'] = message.receive_team.name
    elif message.type == 2:
        data['receive_user_id'] = message.receive_user.id
        data['receive_user_name'] = message.receive_user.username
        if (message.receive_user.avatar.name is None or
                message.receive_user.avatar.name == ""):
            avatar_url2 = None
        else:
            avatar_url2 = settings.BACKEND_URL + message.receive_user.avatar.url
        data['receive_user_avatar'] = avatar_url2
    elif message.type == 3:
        data['receive_group_id'] = message.receive_group.id
        data['receive_group_name'] = message.receive_group.name
        data['receive_team_id'] = message.receive_group.team.id
        data['receive_team_name'] = message.receive_group.team.name
    if num == 0:
        return data
    try:
        if message.message_source == "" or message.message_source is None:
            return data
        message_source = ast.literal_eval(message.message_source)
    except Exception as e:
        return False
    if (not isinstance(message_source, list) or message_source is None
            or message_source == []):
        return data
    for message_source_id in message_source:
        if not Message.objects.filter(id=int(message_source_id)).exists():
            return False
        return_data = recu_message(Message.objects.get(id=message_source_id), user, num - 1)
        if return_data is False:
            return False
        data['message_source'].append(return_data)
    return data


class ChatConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        # 客户端向聊天服务端发送websocket连接的请求时自动触发。
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
        team_list = Team2User.objects.filter(user=user, status__gt=-1)
        try:
            aaa = USER_DICT[user.id]
            for team in team_list:
                room_name = f"t{team.team.id}"
                (async_to_sync(aaa.channel_layer.group_discard)
                 (room_name, aaa.channel_name))
                print("1 > 客户端和聊天服务端开始断开连接, room_name is ", room_name)
            group_list = Group_chat2User.objects.filter(user=user, status__gt=-1)
            for group in group_list:
                room_name = f"g{group.group_chat.id}"
                (async_to_sync(aaa.channel_layer.group_discard)
                 (room_name, aaa.channel_name))
                print("1 > 客户端和聊天服务端开始断开连接, room_name is ", room_name)
        except Exception as e:
            pass
        for team in team_list:
            room_name = f"t{team.team.id}"
            async_to_sync(self.channel_layer.group_add)(room_name, self.channel_name)
            print("1 > 客户端和聊天服务端开始建立连接, room_name is ", room_name)
        group_list = Group_chat2User.objects.filter(user=user, status__gt=-1)
        for group in group_list:
            room_name = f"g{group.group_chat.id}"
            async_to_sync(self.channel_layer.group_add)(room_name, self.channel_name)
            print("1 > 客户端和聊天服务端开始建立连接, room_name is ", room_name)
        try:
            USER_DICT[user.id] = self
            # 将当前连接加入到组中
            print("1 > 客户端进入聊天列表" + str(user.id))
        except Exception as e:
            print(e)
            print("1 > 客户端进入聊天列表失败")

    def websocket_receive(self, message):
        # 客户端基于websocket向聊天服务端发送数据时，自动触发接收消息。
        print(f"2 > 聊天服务端接收客户端的消息, message is {message}")
        recv_data = json.loads(message["text"])
        send_data = {"errno": 0, "errmsg": "发送成功"}
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        if user is None or user is False:
            send_data["errno"] = 1001
            send_data["errmsg"] = "token错误或已过期"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            self.close()
            raise StopConsumer()
        # async_to_sync(self.channel_layer.group_add)(room_name, self.channel_name)
        msg_type = recv_data.get("type")
        if msg_type is None:
            send_data["errno"] = 1002
            send_data["errmsg"] = "消息类型不能为空"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            return
        msg_content = recv_data.get("content")
        msg_file_content = recv_data.get("file_content")
        msg_message_source = recv_data.get("message_source")
        if msg_content is None and msg_file_content is None and msg_message_source is None:
            send_data["errno"] = 1003
            send_data["errmsg"] = "消息内容不能为空"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            return
        if msg_file_content is not None:
            path = msg_file_content.split("/api/v1/media/")[-1]
            path = os.path.join(settings.MEDIA_ROOT, path)
            try:
                with open(path, "rb") as f:
                    file_content = f.read()
                msg_file_content = ContentFile(file_content,name=path)
            except Exception as e:
                print(e)
        if msg_message_source is not None:
            if not isinstance(msg_message_source, list):
                try:
                    msg_message_source = ast.literal_eval(msg_message_source)
                except Exception as e:
                    send_data["errno"] = 1004
                    send_data["errmsg"] = "消息内容不能为空"
                    send_data["data"] = {
                        "msg": msg_message_source,
                        "type": str(type(msg_message_source)),
                        "error": str(e)
                    }
                    send_data = json.dumps(send_data)
                    self.send(text_data=send_data)
                    return
            message_source_list = []
            for message_source_id in msg_message_source:
                if not Message.objects.filter(id=message_source_id).exists():
                    send_data["errno"] = 1005
                    send_data["errmsg"] = "消息内容不能为空"
                    send_data = json.dumps(send_data)
                    self.send(text_data=send_data)
                    return
                message_source_list.append(Message.objects.get(id=message_source_id))
        msg_message_source_str = str(msg_message_source)
        msg_sender_id = recv_data.get("sender_id")
        if msg_sender_id is None or not User.objects.filter(id=msg_sender_id).exists():
            send_data["errno"] = 1004
            send_data["errmsg"] = "发送者id不能为空"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            return
        msg_sender = User.objects.get(id=msg_sender_id)
        receive_team_id = recv_data.get("receive_team_id")
        receive_user_id = recv_data.get("receive_user_id")
        receive_group_id = recv_data.get("receive_group_id")
        if msg_type == 1 and (receive_team_id is None
                              or not Team.objects.filter(id=receive_team_id).exists()):
            send_data["errno"] = 1006
            send_data["errmsg"] = "群聊id不能为空"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            return
        if msg_type == 2 and (receive_user_id is None
                              or not User.objects.filter(id=receive_user_id).exists()):
            send_data["errno"] = 1007
            send_data["errmsg"] = "私聊id不能为空"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            return
        if msg_type == 3 and (receive_group_id is None
                              or not Group_chat.objects.filter(id=receive_group_id).exists()):
            send_data["errno"] = 1008
            send_data["errmsg"] = "群组id不能为空"
            send_data = json.dumps(send_data)
            self.send(text_data=send_data)
            return
        if msg_type == 1:
            receive_team = Team.objects.get(id=receive_team_id)
            msg = Message(type=msg_type, content=msg_content, sender=msg_sender,
                          receive_team=receive_team, file_content=msg_file_content,
                          message_source=msg_message_source_str)
            msg.save()
            if msg_sender.avatar.name == "" or msg_sender.avatar.name is None:
                avatar = None
            else:
                avatar = settings.BACKEND_URL + msg_sender.avatar.url
            room_name = f"t{receive_team.id}"
            if Team2User.objects.filter(user=msg_sender, team=receive_team).exists():
                nick_name = Team2User.objects.get(user=msg_sender, team=receive_team).nickname
            else:
                nick_name = msg_sender.username
            data = recu_message(msg, user, 2)
            data['sender_name'] = nick_name
            if data is False:
                send_data["errno"] = 1008
                send_data["errmsg"] = "发送失败"
                send_data = json.dumps(send_data)
                self.send(text_data=send_data)
                return
            async_to_sync(self.channel_layer.group_add)(room_name, self.channel_name)
            async_to_sync(self.channel_layer.group_send)(room_name,
                                                         {"type": "chat.message",
                                                          "message": json.dumps(data)})
        elif msg_type == 2:
            receive_user = User.objects.get(id=receive_user_id)
            msg = Message(type=msg_type, content=msg_content, sender=msg_sender,
                          receive_user=receive_user, file_content=msg_file_content,
                          message_source=msg_message_source_str)
            msg.save()
            data = recu_message(msg, user, 2)
            if data is False:
                send_data["errno"] = 1009
                send_data["errmsg"] = "发送失败"
                send_data = json.dumps(send_data)
                self.send(text_data=send_data)
                return
            try:
                USER_DICT[receive_user.id].send(text_data=json.dumps(data))
                self.send(text_data=json.dumps(data))
            except Exception as e:
                self.send(text_data=json.dumps(data))
        elif msg_type == 3:
            receive_group = Group_chat.objects.get(id=receive_group_id)
            msg = Message(type=msg_type, content=msg_content, sender=msg_sender,
                          receive_group=receive_group, file_content=msg_file_content,
                          message_source=msg_message_source_str)
            msg.save()
            if msg_sender.avatar.name == "" or msg_sender.avatar.name is None:
                avatar = None
            else:
                avatar = settings.BACKEND_URL + msg_sender.avatar.url
            room_name = f"g{receive_group.id}"
            if Team2User.objects.filter(user=msg_sender, team=receive_group.team).exists():
                nick_name = Team2User.objects.get(user=msg_sender,
                                                  team=receive_group.team).nickname
            else:
                nick_name = msg_sender.username
            data = recu_message(msg, user, 2)
            data['sender_name'] = nick_name
            if data is False:
                send_data["errno"] = 1010
                send_data["errmsg"] = "发送失败"
                send_data = json.dumps(send_data)
                self.send(text_data=send_data)
                return
            async_to_sync(self.channel_layer.group_add)(room_name, self.channel_name)
            async_to_sync(self.channel_layer.group_send)(room_name,
                                                         {"type": "chat.message",
                                                          "message": json.dumps(data)})

    def chat_message(self, event):
        # 聊天服务端向客户端发送消息时自动触发
        print("3 > 聊天服务端向客户端发送消息")
        self.send(text_data=event["message"])

    def websocket_disconnect(self, message):
        """
        客户端与聊天服务端断开websocket连接时自动触发(不管是客户端向聊天服务端断开还是聊天
        服务端向客户端断开都会执行)
        """
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        user = auth_token(params.get("token", [None])[0])
        if user is None or user is False:
            self.close()
            raise StopConsumer()
        team_list = Team2User.objects.filter(user=user, status__gt=-1)
        for team in team_list:
            room_name = f"t{team.team.id}"
            async_to_sync(self.channel_layer.group_discard)(room_name,
                                                            self.channel_name)
            print("4 > 客户端和聊天服务端开始断开连接, room_name is ", room_name)
        group_list = Group_chat2User.objects.filter(user=user, status__gt=-1)
        for group in group_list:
            room_name = f"g{group.group_chat.id}"
            async_to_sync(self.channel_layer.group_discard)(room_name,
                                                            self.channel_name)
            print("4 > 客户端和聊天服务端开始断开连接, room_name is ", room_name)
        try:
            del USER_DICT[user.id]
            # 将当前连接从组中移除
            print("4 > 客户端退出聊天列表" + str(user.id))
        except Exception as e:
            print(e)
            print("4 > 客户端退出聊天列表失败")
        print("5 > 客户端和聊天服务端断开连接")
        self.close()
        raise StopConsumer()
