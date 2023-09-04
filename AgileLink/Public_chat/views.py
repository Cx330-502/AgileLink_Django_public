import ast
import json
from datetime import datetime

from django.http import JsonResponse

from Notice_center.consumers import USER_DICT2
from Public_chat.consumers import *
from Agile_models.models import *


def get_message(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    message_id = body.get('message_id')
    if message_id is None or not Message.objects.filter(id=message_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '消息不存在'})
    message = Message.objects.get(id=message_id)
    data = recu_message(message, user, 2)
    if data is False:
        return JsonResponse({'errno': 1004, 'errmsg': '消息源错误'})
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': data})


def login_get_messages(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    print(type(body.get('token')))
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    data = {}
    data['team_list'] = []
    data['private_chat_list'] = []
    team2user_list = Team2User.objects.filter(user=user, status__gt=-1)
    for team2user in team2user_list:
        exit_time = team2user.exit_time
        message_num = Message.objects.filter(receive_team=team2user.team, type=1,
                                             send_time__gt=exit_time).count()
        try:
            last_message = Message.objects.filter(receive_team=team2user.team,
                                                  type=1).order_by('-send_time')[0]
            if (last_message.file_content.name is None or
                    last_message.file_content.name == ""):
                url = ""
            else:
                url = settings.BACKEND_URL + last_message.file_content.url
            if (last_message.sender.avatar.name is None or
                    last_message.sender.avatar.name == ""):
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + last_message.sender.avatar.url
            if Team2User.objects.filter(user=last_message.sender,
                                        team=team2user.team).exists():
                nick_name = Team2User.objects.get(user=last_message.sender,
                                                  team=team2user.team).nickname
            else:
                nick_name = last_message.sender.username
            last_message0 = recu_message(last_message, user, 2)
            if last_message0 is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            last_message0['sender_name'] = nick_name
        except Exception as e:
            print(e)
            last_message0 = {'content': ''}

        data['team_list'].append({
            'team_id': team2user.team.id,
            'team_name': team2user.team.name,
            'message_num': message_num,
            'last_message': last_message0
        })
    people_list1 = Message.objects.filter(sender=user,
                                          type=2).values('receive_user').distinct()
    people_list2 = Message.objects.filter(receive_user=user,
                                          type=2).values('sender').distinct()
    people_list = set()
    for people in people_list1:
        people_list.add(User.objects.get(id=people['receive_user']))
    for people in people_list2:
        people_list.add(User.objects.get(id=people['sender']))
    people_list = list(people_list)
    for people in people_list:
        message_num = Message.objects.filter(sender=people, receive_user=user, type=2,
                                             read_status=0).count()
        try:
            last_message1 = Message.objects.filter(sender=people, receive_user=user,
                                                   type=2).order_by('-send_time')[0]
        except Exception as e:
            last_message1 = None
        try:
            last_message2 = Message.objects.filter(sender=user, receive_user=people,
                                                   type=2).order_by('-send_time')[0]
        except Exception as e:
            last_message2 = None
        if (last_message1 is not None and
                last_message2 is not None and
                last_message1.send_time > last_message2.send_time):
            last_message = last_message1
        elif (last_message1 is not None and
              last_message2 is not None and
              last_message1.send_time < last_message2.send_time):
            last_message = last_message2
        elif last_message1 is not None and last_message2 is None:
            last_message = last_message2
        elif last_message1 is None and last_message2 is not None:
            last_message = last_message2
        else:
            last_message = None
        if last_message is not None:
            if (last_message.file_content.name is None or
                    last_message.file_content.name == ""):
                url = ""
            else:
                url = settings.BACKEND_URL + last_message.file_content.url
            if (last_message.sender.avatar.name is None or
                    last_message.sender.avatar.name == ""):
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + last_message.sender.avatar.url
            if (last_message.receive_user.avatar.name is None or
                    last_message.receive_user.avatar.name == ""):
                avatar_url2 = None
            else:
                avatar_url2 = settings.BACKEND_URL + last_message.receive_user.avatar.url
            last_message0 = recu_message(last_message, user, 2)
        else:
            last_message0 = {'content': ''}
        data['private_chat_list'].append({
            'people_id': people.id,
            'people_name': people.username,
            'message_num': message_num,
            'last_message': last_message0
        })
    group2user_list = Group_chat2User.objects.filter(user=user, status__gt=-1)
    data['group_chat_list'] = []
    for group2user in group2user_list:
        exit_time = group2user.exit_time
        message_num = Message.objects.filter(receive_group=group2user.group_chat, type=3,
                                             send_time__gt=exit_time).count()
        try:
            last_message = Message.objects.filter(receive_group=group2user.group_chat,
                                                  type=3).order_by('-send_time')[0]
            last_message0 = recu_message(last_message, user, 2)
            if last_message0 is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            if Team2User.objects.filter(user=last_message.sender,
                                        team=group2user.group_chat.team).exists():
                nick_name = Team2User.objects.get(user=last_message.sender,
                                                  team=group2user.group_chat.team).nickname
            else:
                nick_name = last_message.sender.username
            last_message0['sender_name'] = nick_name
        except Exception as e:
            last_message0 = {'content': ''}
        data['group_chat_list'].append({
            'group_id': group2user.group_chat.id,
            'group_name': group2user.group_chat.name,
            'message_num': message_num,
            'last_message': last_message0
        })
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': data})


def get_new_messages(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    type0 = body.get("type")
    if type is None:
        return JsonResponse({'errno': 1003, 'errmsg': '请求类型不能为空'})
    type2 = body.get("type2")
    if type2 is None:
        return JsonResponse({'errno': 1006, 'errmsg': '请选择是先于还是晚于'})
    if type0 == 1:
        team_id = body.get('team_id')
        if not Team.objects.filter(id=team_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '团队不存在'})
        team = Team.objects.get(id=team_id)
        time0 = body.get('time')
        if time0 is None:
            return JsonResponse({'errno': 1005, 'errmsg': '时间不能为空'})
        if type2 == 1:
            message_list = Message.objects.filter(
                receive_team=team, send_time__lt=time0).order_by('-send_time')[:20]
        else:
            message_list = Message.objects.filter(
                receive_team=team, send_time__gt=time0).order_by('send_time')[:20]
        return_list = []
        for message in message_list:
            if message.file_content.name is None or message.file_content.name == "":
                url = ""
            else:
                url = message.file_content.url
            if message.sender.avatar.name is None or message.sender.avatar.name == "":
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + message.sender.avatar.url
            if Team2User.objects.filter(user=message.sender, team=team).exists():
                nick_name = Team2User.objects.get(user=message.sender, team=team).nickname
            else:
                nick_name = message.sender.username
            temp = recu_message(message, user, 2)
            if temp is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            temp['sender_name'] = nick_name
            return_list.append(temp)
        return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': {'message_list':
                                                                            return_list}})
    elif type0 == 2:
        receive_user_id = body.get('receive_user_id')
        if not User.objects.filter(id=receive_user_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '用户不存在'})
        receive_user = User.objects.get(id=receive_user_id)
        time0 = body.get('time')
        if time0 is None:
            return JsonResponse({'errno': 1005, 'errmsg': '时间不能为空'})
        if type2 == 1:
            message_list1 = Message.objects.filter(
                sender=user, receive_user=receive_user, send_time__lt=time0).order_by(
                '-send_time')[:20]
            message_list2 = Message.objects.filter(
                sender=receive_user, receive_user=user, send_time__lt=time0).order_by(
                '-send_time')[:20]
        else:
            message_list1 = Message.objects.filter(
                sender=user, receive_user=receive_user, send_time__gt=time0).order_by(
                'send_time')[:20]
            message_list2 = Message.objects.filter(
                sender=receive_user, receive_user=user, send_time__gt=time0).order_by(
                'send_time')[:20]
        combined_list = list(message_list1) + list(message_list2)
        if type2 == 1:
            sorted_list = sorted(combined_list, key=lambda x: x.send_time, reverse=True)
        else:
            sorted_list = sorted(combined_list, key=lambda x: x.send_time)
        message_list = sorted_list[:20]
        return_list = []
        for message in message_list:
            if message.file_content.name is None or message.file_content.name == "":
                url = ""
            else:
                url = message.file_content.url
            if message.sender.avatar.name is None or message.sender.avatar.name == "":
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + message.sender.avatar.url
            if (message.receive_user.avatar.name is None or
                    message.receive_user.avatar.name == ""):
                avatar_url2 = None
            else:
                avatar_url2 = settings.BACKEND_URL + message.receive_user.avatar.url
            temp = recu_message(message, user, 2)
            if temp is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            return_list.append(temp)
        return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': {'message_list':
                                                                            return_list}})
    elif type0 == 3:
        group_id = body.get('receive_group_id')
        if not Group_chat.objects.filter(id=group_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '群组不存在'})
        group_chat = Group_chat.objects.get(id=group_id)
        time0 = body.get('time')
        if time0 is None:
            return JsonResponse({'errno': 1005, 'errmsg': '时间不能为空'})
        if type2 == 1:
            message_list = Message.objects.filter(
                receive_group=group_chat, send_time__lt=time0).order_by('-send_time')[:20]
        else:
            message_list = Message.objects.filter(
                receive_group=group_chat, send_time__gt=time0).order_by('send_time')[:20]
        return_list = []
        for message in message_list:
            if message.file_content.name is None or message.file_content.name == "":
                url = ""
            else:
                url = message.file_content.url
            if message.sender.avatar.name is None or message.sender.avatar.name == "":
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + message.sender.avatar.url
            if Team2User.objects.filter(user=message.sender, team=group_chat.team).exists():
                nick_name = Team2User.objects.get(user=message.sender,
                                                  team=group_chat.team).nickname
            else:
                nick_name = message.sender.username
            temp = recu_message(message, user, 2)
            temp['sender_name'] = nick_name
            if temp is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            return_list.append(temp)
        return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': {'message_list':
                                                                            return_list}})


def exit_chat(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    type0 = body.get("type")
    if type0 is None:
        return JsonResponse({'errno': 1003, 'errmsg': '请求类型不能为空'})
    if type0 == 1:
        team_id = body.get('team_id')
        if not Team.objects.filter(id=team_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '团队不存在'})
        team = Team.objects.get(id=team_id)
        try:
            team2user = Team2User.objects.get(team=team, user=user)
        except Exception as e:
            return JsonResponse({'errno': 1005, 'errmsg': '您不在该团队中'})
        team2user.exit_time = datetime.now()
        team2user.save()
        return JsonResponse({'errno': 0, 'errmsg': '退出成功'})
    elif type0 == 2:
        receive_user_id = body.get('receive_user_id')
        if not User.objects.filter(id=receive_user_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '用户不存在'})
        receive_user = User.objects.get(id=receive_user_id)
        try:
            message_list1 = Message.objects.filter(sender=user,
                                                   receive_user=receive_user, read_status=0)
            message_list2 = Message.objects.filter(sender=receive_user,
                                                   receive_user=user, read_status=0)
            message_list = list(message_list1) + list(message_list2)
            for message in message_list:
                message.read_status = 1
                message.save()
        except Exception as e:
            return JsonResponse({'errno': 1005, 'errmsg': '您不在该私聊中'})
        return JsonResponse({'errno': 0, 'errmsg': '退出成功'})
    elif type0 == 3:
        receive_group_id = body.get('receive_group_id')
        if not Group_chat.objects.filter(id=receive_group_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '群组不存在'})
        group_chat = Group_chat.objects.get(id=receive_group_id)
        try:
            group2user = Group_chat2User.objects.get(group_chat=group_chat, user=user)
        except Exception as e:
            return JsonResponse({'errno': 1005, 'errmsg': '您不在该群组中'})
        group2user.exit_time = datetime.now()
        group2user.save()
        return JsonResponse({'errno': 0, 'errmsg': '退出成功'})


def search_message(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    type0 = body.get("type")
    if type0 is None:
        return JsonResponse({'errno': 1003, 'errmsg': '请求类型不能为空'})
    time0 = body.get('time')
    if time0 is None:
        return JsonResponse({'errno': 1007, 'errmsg': '时间不能为空'})
    keyword = body.get('keyword')
    if keyword is None:
        return JsonResponse({'errno': 1006, 'errmsg': '关键词不能为空'})
    if type0 == 1:
        team_id = body.get('team_id')
        if not Team.objects.filter(id=team_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '团队不存在'})
        team = Team.objects.get(id=team_id)
        try:
            team2user = Team2User.objects.get(team=team, user=user)
        except Exception as e:
            return JsonResponse({'errno': 1005, 'errmsg': '您不在该团队中'})
        message_list = Message.objects.filter(
            receive_team=team, content__contains=keyword, send_time__lt=time0
        ).order_by('send_time')[:20]
        return_list = []
        for message in message_list:
            if message.file_content.name is None or message.file_content.name == "":
                url = ""
            else:
                url = message.file_content.url
            if message.sender.avatar.name is None or message.sender.avatar.name == "":
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + message.sender.avatar.url
            if Team2User.objects.filter(user=message.sender, team=team).exists():
                nick_name = Team2User.objects.get(user=message.sender, team=team).nickname
            else:
                nick_name = message.sender.username
            temp = recu_message(message, user, 2)
            if temp is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            temp['sender_name'] = nick_name
            return_list.append(temp)
        return JsonResponse({'errno': 0, 'errmsg': '获取成功',
                             'data': {'message_list': return_list}})
    elif type0 == 2:
        receive_user_id = body.get('receive_user_id')
        if not User.objects.filter(id=receive_user_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '用户不存在'})
        receive_user = User.objects.get(id=receive_user_id)
        try:
            message_list1 = Message.objects.filter(
                sender=user, receive_user=receive_user, content__contains=keyword,
                send_time__lt=time0).order_by('send_time')[:20]
            message_list2 = Message.objects.filter(
                sender=receive_user, receive_user=user, content__contains=keyword,
                send_time__lt=time0).order_by('send_time')[:20]
            combined_list = list(message_list1) + list(message_list2)
            sorted_list = sorted(combined_list, key=lambda x: x.send_time)
            message_list = sorted_list[:20]
            return_list = []
            for message in message_list:
                if message.file_content.name is None or message.file_content.name == "":
                    url = ""
                else:
                    url = message.file_content.url
                if message.sender.avatar.name is None or message.sender.avatar.name == "":
                    avatar_url = None
                else:
                    avatar_url = settings.BACKEND_URL + message.sender.avatar.url
                if (message.receive_user.avatar.name is None
                        or message.receive_user.avatar.name == ""):
                    avatar_url2 = None
                else:
                    avatar_url2 = settings.BACKEND_URL + message.receive_user.avatar.url
                temp = recu_message(message, user, 2)
                if temp is False:
                    return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
                return_list.append(temp)
                return JsonResponse({'errno': 0, 'errmsg': '获取成功',
                                     'data': {'message_list': return_list}})
        except Exception as e:
            return JsonResponse({'errno': 1005, 'errmsg': '您不在该私聊中'})
    elif type0 == 3:
        group_id = body.get('group_id')
        if not Group_chat.objects.filter(id=group_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '群组不存在'})
        group_chat = Group_chat.objects.get(id=group_id)
        try:
            group2user = Group_chat2User.objects.get(group_chat=group_chat, user=user)
        except Exception as e:
            return JsonResponse({'errno': 1005, 'errmsg': '您不在该群组中'})
        message_list = Message.objects.filter(
            receive_group=group_chat, content__contains=keyword, send_time__lt=time0
        ).order_by('-send_time')[:20]
        return_list = []
        for message in message_list:
            if message.file_content.name is None or message.file_content.name == "":
                url = ""
            else:
                url = message.file_content.url
            if message.sender.avatar.name is None or message.sender.avatar.name == "":
                avatar_url = None
            else:
                avatar_url = settings.BACKEND_URL + message.sender.avatar.url
            temp = recu_message(message, user, 2)
            if temp is False:
                return JsonResponse({'errno': 1007, 'errmsg': '消息源错误'})
            if Team2User.objects.filter(user=message.sender, team=group_chat.team).exists():
                nick_name = Team2User.objects.get(user=message.sender,
                                                  team=group_chat.team).nickname
            else:
                nick_name = message.sender.username
            temp['sender_name'] = nick_name
            return_list.append(temp)
        return JsonResponse({'errno': 0, 'errmsg': '获取成功',
                             'data': {'message_list': return_list}})


def create_group(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '团队id不能为空'})
    team = Team.objects.get(id=team_id)
    group_name = body.get('group_name')
    if group_name is None:
        return JsonResponse({'errno': 1003, 'errmsg': '群组名称不能为空'})
    if Group_chat.objects.filter(team=team, name=group_name).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '群组名称已存在'})
    introduction = body.get('group_introduction')
    group_chat = Group_chat(team=team, name=group_name, creator=user,
                            introduction=introduction)
    group_chat.save()
    Group_chat2User.objects.create(group_chat=group_chat, user=user, status=2)
    data = {
        'group_id': group_chat.id,
        'group_name': group_chat.name,
        'introduction': group_chat.introduction,
        'creator_id': group_chat.creator.id,
        'creator_name': group_chat.creator.username,
        'creator_avatar': settings.BACKEND_URL + group_chat.creator.avatar.url,
    }
    return JsonResponse({'errno': 0, 'errmsg': '创建成功', 'data': data})


def edit_group(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token(body.get('token'))
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '群组id不能为空'})
    group_chat = Group_chat.objects.get(id=group_id)
    if not Group_chat2User.objects.filter(group_chat=group_chat,
                                          user=user, status=2).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '您不在该群组中或权限不足'})
    group_name = body.get('group_name')
    introduction = body.get('group_introduction')
    if group_name is not None and group_name != "":
        if Group_chat.objects.filter(team=group_chat.team, name=group_name).exists():
            return JsonResponse({'errno': 1005, 'errmsg': '群组名称已存在'})
        group_chat.name = group_name
    if introduction is not None and introduction != "":
        group_chat.introduction = introduction
    group_chat.save()
    data = {
        'group_id': group_chat.id,
        'group_name': group_chat.name,
        'introduction': group_chat.introduction,
    }
    return JsonResponse({'errno': 0, 'errmsg': '修改成功', 'data': data})


def get_group_list(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '团队id不能为空'})
    team = Team.objects.get(id=team_id)
    group_chat_list = Group_chat2User.objects.filter(user=user, status__gt=-1)
    data = []
    for group_chat2user in group_chat_list:
        data0 = {
            'group_id': group_chat2user.group_chat.id,
            'group_name': group_chat2user.group_chat.name,
            'introduction': group_chat2user.group_chat.introduction,
            'creator_id': group_chat2user.group_chat.creator.id,
            'creator_name': group_chat2user.group_chat.creator.username,
            'creator_avatar': settings.BACKEND_URL +
                              group_chat2user.group_chat.creator.avatar.url,
            'status': group_chat2user.status
        }
        data.append(data0)
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': data})


def invite_member(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '群组id不能为空'})
    group_chat = Group_chat.objects.get(id=group_id)
    if not Group_chat2User.objects.filter(group_chat=group_chat,
                                          user=user, status=2).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '您不在该群组中或权限不足'})
    invitee_id = body.get('invitee_id')
    if invitee_id is None or not User.objects.filter(id=invitee_id).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '被邀请人id不能为空'})
    invitee = User.objects.get(id=invitee_id)
    if Group_chat2User.objects.filter(group_chat=group_chat, user=invitee).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '该用户已在群组中'})
    Group_chat2User.objects.create(group_chat=group_chat, user=invitee, status=1)
    notice = Notice(sender=user, receiver=invitee, type=11, content=
    "%s邀请您加入群组%s" % (user.username, group_chat.name),
                    group_chat_source=group_chat)
    notice.save()
    data = {
        'notice_id': notice.id,
        'notice_type': notice.type,
        'send_time': notice.send_time.strftime('%Y-%m-%d %H:%M:%S'),
        'group_id': group_chat.id,
        'group_name': group_chat.name,
        'introduction': group_chat.introduction,
        'creator_id': group_chat.creator.id,
        'creator_name': group_chat.creator.username,
        'creator_avatar': settings.BACKEND_URL + group_chat.creator.avatar.url,
        'receiver_id': invitee.id,
        'receiver_name': invitee.username,
        'content': notice.content,
    }
    try:
        room_name = f"g{group_chat.id}"
        (async_to_sync(USER_DICT[invitee_id].channel_layer.group_add)
         (room_name, USER_DICT[invitee_id].channel_name))
        print("6 > 客户端成功加入聊天服务端" + room_name)
    except Exception as e:
        print("6 > 客户端加入聊天服务端失败")
        print(e)
    try:
        USER_DICT2[invitee.id].send(json.dumps(data))
    except Exception as e:
        return JsonResponse({'errno': 1007, 'errmsg': '邀请成功，但被邀请人不在线'})
    return JsonResponse({'errno': 0, 'errmsg': '邀请成功'})


def exit_group(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '群组id不能为空'})
    group_chat = Group_chat.objects.get(id=group_id)
    if not Group_chat2User.objects.filter(group_chat=group_chat,
                                          user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '您不在该群组中'})
    group_chat2user = Group_chat2User.objects.get(group_chat=group_chat, user=user)
    group_chat2user.delete()
    notice = Notice(sender=user, receiver=group_chat.creator, type=15, content=
    "%s退出了群组%s" % (user.username, group_chat.name),
                    group_chat_source=group_chat)
    notice.save()
    data = {
        'notice_id': notice.id,
        'notice_type': notice.type,
        'send_time': notice.send_time.strftime('%Y-%m-%d %H:%M:%S'),
        'group_id': group_chat.id,
        'group_name': group_chat.name,
        'introduction': group_chat.introduction,
        'creator_id': group_chat.creator.id,
        'creator_name': group_chat.creator.username,
        'creator_avatar': settings.BACKEND_URL + group_chat.creator.avatar.url,
        'receiver_id': group_chat.creator.id,
        'receiver_name': group_chat.creator.username,
        'content': notice.content,
    }
    try:
        USER_DICT2[group_chat.creator.id].send(json.dumps(data))
    except Exception as e:
        return JsonResponse({'errno': 1006, 'errmsg': '退出成功，但群主不在线'})
    try:
        room_name = f"g{group_chat.id}"
        (async_to_sync(USER_DICT[group_chat.creator.id].channel_layer.group_discard)
         (room_name, USER_DICT[group_chat.creator.id].channel_name))
        print("6 > 客户端成功退出聊天服务端" + room_name)
    except Exception as e:
        print("6 > 客户端退出聊天服务端失败")
        print(e)
    return JsonResponse({'errno': 0, 'errmsg': '退出成功'})


def get_group_member_list(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '群组id不能为空'})
    group_chat = Group_chat.objects.get(id=group_id)
    if not Group_chat2User.objects.filter(group_chat=group_chat,
                                          user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '您不在该群组中'})
    group_chat2user_list = Group_chat2User.objects.filter(group_chat=group_chat)
    data = []
    for group_chat2user in group_chat2user_list:
        data0 = {
            'user_id': group_chat2user.user.id,
            'user_name': group_chat2user.user.username,
            'user_avatar': settings.BACKEND_URL + group_chat2user.user.avatar.url,
            'status': group_chat2user.status
        }
        data.append(data0)
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': data})


def dismiss_group(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '群组id不能为空'})
    group_chat = Group_chat.objects.get(id=group_id)
    if group_chat.creator != user:
        return JsonResponse({'errno': 1004, 'errmsg': '您不是群主'})
    group_chat2user_list = Group_chat2User.objects.filter(group_chat=group_chat)
    for group_chat2user in group_chat2user_list:
        notice = Notice(sender=user, receiver=group_chat2user.user, type=16, content=
        "群主解散了群组%s" % group_chat.name,
                        group_chat_source=group_chat)
        notice.save()
        data = {
            'notice_id': notice.id,
            'notice_type': notice.type,
            'send_time': notice.send_time.strftime('%Y-%m-%d %H:%M:%S'),
            'group_id': group_chat.id,
            'group_name': group_chat.name,
            'introduction': group_chat.introduction,
            'creator_id': group_chat.creator.id,
            'creator_name': group_chat.creator.username,
            'creator_avatar': settings.BACKEND_URL + group_chat.creator.avatar.url,
            'receiver_id': group_chat2user.user.id,
            'receiver_name': group_chat2user.user.username,
            'content': notice.content,
        }
        try:
            USER_DICT2[group_chat2user.user.id].send(json.dumps(data))
        except Exception as e:
            pass
        group_chat2user.delete()
    group_chat.delete()
    return JsonResponse({'errno': 0, 'errmsg': '解散成功'})