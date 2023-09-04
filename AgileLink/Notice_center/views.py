from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from Notice_center.consumers import *
from Public_chat.consumers import recu_message
from Public_chat.models import *
from Agile_models.models import *


# Create your views here.

def team_at(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '团队id不能为空'})
    team = Team.objects.get(id=team_id)
    ated_user_id = body.get('ated_user_id')
    if ated_user_id is None or not User.objects.filter(id=ated_user_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '被@用户id不能为空'})
    ated_user = User.objects.get(id=ated_user_id)
    if not Team2User.objects.filter(team=team, user=user).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '用户不在该团队中'})
    if not Team2User.objects.filter(team=team, user=ated_user).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '被@用户不在该团队中'})
    content = body.get('content')
    if content is None:
        return JsonResponse({'errno': 1007, 'errmsg': '消息内容不能为空'})
    message_source_id = body.get('message_source_id')
    if message_source_id is None or not Message.objects.filter(id=message_source_id).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '消息id不能为空'})
    if Team2User.objects.filter(team=team, user=user, status__gt=0).exists():
        nick_name = Team2User.objects.get(team=team, user=user).nickname
    else:
        nick_name = user.username
    notice = Notice(
        type=8,
        content="用户" + nick_name + "在团队" + team.name + "中@了你",
        sender=user,
        receiver=ated_user,
        team_source=team,
        message_source=Message.objects.get(id=message_source_id),
        send_time=timezone.now(),
        read_status=1
    )
    notice.save()
    if user.avatar.name is None or user.avatar.name == '':
        avatar = None
    else:
        avatar = settings.BACKEND_URL + user.avatar.url
    data = {
        'type': 8,
        'content': "用户" + nick_name + "在团队" + team.name + "中@了你",
        'msg_content': content,
        'sender_id': user.id,
        'sender_name': nick_name,
        'sender_username': user.username,
        'sender_avatar': avatar,
        'receiver_id': ated_user.id,
        'team_source_id': team.id,
        'message_source_id': message_source_id,
        'message': recu_message(Message.objects.get(id=message_source_id), user, 2),
        'send_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'notice_id': notice.id,
    }
    try:
        print("111111111111111")
        USER_DICT2[ated_user.id].send(text_data=json.dumps(data))
        print("222222222222222")
        print(USER_DICT2)
    except Exception as e:
        return JsonResponse({'errno': 1009, 'errmsg': str(e)})
        pass
    return JsonResponse({'errno': 0, 'errmsg': '@成功'})


def team_at_all(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '团队id不能为空'})
    team = Team.objects.get(id=team_id)
    if not Team2User.objects.filter(team=team, user=user, status__gt=1).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '用户权限不够'})
    content = body.get('content')
    if content is None:
        return JsonResponse({'errno': 1007, 'errmsg': '消息内容不能为空'})
    message_source_id = body.get('message_source_id')
    if message_source_id is None or not Message.objects.filter(id=message_source_id).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '消息id不能为空'})
    team2user_list = Team2User.objects.filter(team=team)
    for team2user in team2user_list:
        ated_user = team2user.user
        if ated_user == user:
            continue
        if Team2User.objects.filter(team=team, user=user).exists():
            nick_name = Team2User.objects.get(team=team, user=user).nickname
        else:
            nick_name = user.username
        notice = Notice(
            type=9,
            content="用户" + nick_name + "在团队" + team.name + "中@了你",
            sender=user,
            receiver=ated_user,
            team_source=team,
            message_source=Message.objects.get(id=message_source_id),
            send_time=timezone.now(),
            read_status=1
        )
        notice.save()
        if user.avatar.name is None or user.avatar.name == '':
            avatar = None
        else:
            avatar = settings.BACKEND_URL + user.avatar.url
        data = {
            'type': 9,
            'content': "用户" + nick_name + "在团队" + team.name + "中@了你",
            'msg_content': content,
            'sender_id': user.id,
            'sender_name': nick_name,
            'sender_username': user.username,
            'sender_avatar': avatar,
            'receiver_id': ated_user.id,
            'team_source_id': team.id,
            'message_source_id': message_source_id,
            'message': recu_message(Message.objects.get(id=message_source_id), user, 2),
            'send_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            'notice_id': notice.id,
        }
        try:
            USER_DICT2[ated_user.id].send(text_data=json.dumps(data))
        except:
            pass
    return JsonResponse({'errno': 0, 'errmsg': '@成功'})


def doc_at(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    doc_id = body.get('doc_id')
    if doc_id is None or not Documents.objects.filter(id=doc_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '文档id不能为空'})
    doc = Documents.objects.get(id=doc_id)
    ated_user_id = body.get('ated_user_id')
    if ated_user_id is None or not User.objects.filter(id=ated_user_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '被@用户id不能为空'})
    ated_user = User.objects.get(id=ated_user_id)
    if Team2User.objects.filter(team=doc.project.team, user=user).exists():
        nick_name = Team2User.objects.get(team=doc.project.team, user=user).nickname
    else:
        nick_name = user.username
    content = ("用户" + nick_name + "在" + doc.project.team.name
               + "团队的" + doc.project.name + "项目的文档" + doc.name + "中@了你")
    notice = Notice(
        type=10,
        content=content,
        sender=user,
        receiver=ated_user,
        doc_source=doc,
        send_time=timezone.now(),
        read_status=1
    )
    notice.save()
    if user.avatar.name is None or user.avatar.name == '':
        avatar = None
    else:
        avatar = settings.BACKEND_URL + user.avatar.url
    data = {
        'type': 10,
        'content': content,
        'sender_id': user.id,
        'sender_name': nick_name,
        'sender_username': user.username,
        'sender_avatar': avatar,
        'receiver_id': ated_user.id,
        'doc_source_id': doc.id,
        'send_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'team_id': doc.project.team.id,
        'team_name': doc.project.team.name,
        'project_id': doc.project.id,
        'project_name': doc.project.name,
        'notice_id': notice.id,
    }
    try:
        USER_DICT2[ated_user.id].send(text_data=json.dumps(data))
    except:
        pass
    return JsonResponse({'errno': 0, 'errmsg': '@成功'})


def group_at(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '群组id不能为空'})
    group = Group_chat.objects.get(id=group_id)
    ated_user_id = body.get('ated_user_id')
    if ated_user_id is None or not User.objects.filter(id=ated_user_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '被@用户id不能为空'})
    ated_user = User.objects.get(id=ated_user_id)
    if not Group_chat2User.objects.filter(group_chat=group, user=user).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '用户不在该群组中'})
    if not Group_chat2User.objects.filter(group_chat=group, user=ated_user).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '被@用户不在该群组中'})
    content = body.get('content')
    if content is None:
        return JsonResponse({'errno': 1007, 'errmsg': '消息内容不能为空'})
    message_source_id = body.get('message_source_id')
    if message_source_id is None or not Message.objects.filter(id=message_source_id).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '消息id不能为空'})
    notice = Notice(
        type=12,
        content="用户" + user.username + "在群组" + group.name + "中@了你",
        sender=user,
        receiver=ated_user,
        group_chat_source=group,
        message_source=Message.objects.get(id=message_source_id),
        send_time=timezone.now(),
        read_status=1
    )
    notice.save()
    if user.avatar.name is None or user.avatar.name == '':
        avatar = None
    else:
        avatar = settings.BACKEND_URL + user.avatar.url
    data = {
        'type': 12,
        'content': "用户" + user.username + "在团队" + group.name + "中@了你",
        'msg_content': content,
        'sender_id': user.id,
        'sender_name': user.username,
        'sender_username': user.username,
        'sender_avatar': avatar,
        'receiver_id': ated_user.id,
        'group_source_id': group.id,
        'group_source_name': group.name,
        'message_source_id': message_source_id,
        'message': recu_message(Message.objects.get(id=message_source_id), user, 2),
        'send_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'notice_id': notice.id,
    }
    try:
        USER_DICT2[ated_user.id].send(text_data=json.dumps(data))
    except Exception as e:
        return JsonResponse({'errno': 1009, 'errmsg': '@成功,但对方不在线'})
        pass
    return JsonResponse({'errno': 0, 'errmsg': '@成功'})


def group_at_all(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    group_id = body.get('group_id')
    if group_id is None or not Group_chat.objects.filter(id=group_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '群组id不能为空'})
    group = Group_chat.objects.get(id=group_id)
    if not Group_chat2User.objects.filter(group_chat=group, user=user).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '用户不在该群组中'})
    content = body.get('content')
    if content is None:
        return JsonResponse({'errno': 1007, 'errmsg': '消息内容不能为空'})
    message_source_id = body.get('message_source_id')
    if message_source_id is None or not Message.objects.filter(id=message_source_id).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '消息id不能为空'})
    group2user_list = Group_chat2User.objects.filter(group_chat=group)
    for group2user in group2user_list:
        ated_user = group2user.user
        notice = Notice(
            type=13,
            content="用户" + user.username + "在群组" + group.name + "中@了你",
            sender=user,
            receiver=ated_user,
            group_chat_source=group,
            message_source=Message.objects.get(id=message_source_id),
            send_time=timezone.now(),
            read_status=1
        )
        notice.save()
        if user.avatar.name is None or user.avatar.name == '':
            avatar = None
        else:
            avatar = settings.BACKEND_URL + user.avatar.url
        data = {
            'type': 13,
            'content': "用户" + user.username + "在团队" + group.name + "中@了你",
            'msg_content': content,
            'sender_id': user.id,
            'sender_name': user.username,
            'sender_username': user.username,
            'sender_avatar': avatar,
            'receiver_id': ated_user.id,
            'group_source_id': group.id,
            'group_source_name': group.name,
            'message_source_id': message_source_id,
            'message': recu_message(Message.objects.get(id=message_source_id), user, 2),
            'send_time': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            'notice_id': notice.id,
        }
        try:
            USER_DICT2[ated_user.id].send(text_data=json.dumps(data))
        except Exception as e:
            return JsonResponse({'errno': 1009, 'errmsg': '@成功,但对方不在线'})
            pass
    return JsonResponse({'errno': 0, 'errmsg': '@全体成功'})


def read_notice(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    notice_id_list = body.get('notice_id_list')
    if notice_id_list is None or notice_id_list == []:
        return JsonResponse({'errno': 1003, 'errmsg': '消息id列表不能为空'})
    for notice_id in notice_id_list:
        if not Notice.objects.filter(id=notice_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '消息id不存在'})
        notice = Notice.objects.get(id=notice_id)
        if notice.receiver != user:
            return JsonResponse({'errno': 1005, 'errmsg': '用户没有权限'})
        notice.read_status = -1
        notice.save()
    return JsonResponse({'errno': 0, 'errmsg': '已读成功'})


def get_unread_notice(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    notice_list = Notice.objects.filter(receiver=user, read_status=1).all()
    data = {"unread_notice_num": notice_list.count(), "unread_notice_list": []}
    for notice in notice_list:
        if notice.receiver != user:
            return JsonResponse({'errno': 1003, 'errmsg': '用户没有权限'})
        if notice.sender.avatar.name is None or notice.sender.avatar.name == "":
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + notice.sender.avatar.url

        notice0 = {
            'notice_id': notice.id,
            'type': notice.type,
            'content': notice.content,
            'sender_id': notice.sender.id,
            'sender_name': notice.sender.username,
            'sender_avatar': avatar_url,
            'receiver_id': notice.receiver.id,
            'send_time': notice.send_time.strftime("%Y-%m-%d %H:%M:%S"),
            'read_status': notice.read_status,
            'doc_source_id': None,
            'doc_source_name': None,
            'project_source_id': None,
            'project_source_name': None,
            'team_source_id': None,
            'team_source_name': None,
            'message': None,
        }
        if notice.doc_source is not None:
            notice0['doc_source_id'] = notice.doc_source.id
            notice0['doc_source_name'] = notice.doc_source.name
            notice0['project_source_id'] = notice.doc_source.project.id
            notice0['project_source_name'] = notice.doc_source.project.name
        if notice.team_source is not None:
            notice0['team_source_id'] = notice.team_source.id
            notice0['team_source_name'] = notice.team_source.name
        if notice.message_source is not None:
            message0 = recu_message(notice.message_source, user, 2)
            if message0 is False:
                message0 = None
            notice0['message'] = message0
        data["unread_notice_list"].append(notice0)
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': data})


def get_readed_notice(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    notice_list = Notice.objects.filter(receiver=user, read_status=-1).all()
    data = {"unread_notice_num": notice_list.count(), "unread_notice_list": []}
    for notice in notice_list:
        if notice.receiver != user:
            return JsonResponse({'errno': 1003, 'errmsg': '用户没有权限'})
        if notice.sender.avatar.name is None or notice.sender.avatar.name == "":
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + notice.sender.avatar.url
        notice0 = {
            'notice_id': notice.id,
            'type': notice.type,
            'content': notice.content,
            'sender_id': notice.sender.id,
            'sender_name': notice.sender.username,
            'sender_avatar': avatar_url,
            'receiver_id': notice.receiver.id,
            'send_time': notice.send_time.strftime("%Y-%m-%d %H:%M:%S"),
            'read_status': notice.read_status,
            'doc_source_id': None,
            'doc_source_name': None,
            'project_source_id': None,
            'project_source_name': None,
            'team_source_id': None,
            'team_source_name': None,
            'message': None,
        }
        if notice.doc_source is not None:
            notice0['doc_source_id'] = notice.doc_source.id
            notice0['doc_source_name'] = notice.doc_source.name
            notice0['project_source_id'] = notice.doc_source.project.id
            notice0['project_source_name'] = notice.doc_source.project.name
        if notice.team_source is not None:
            notice0['team_source_id'] = notice.team_source.id
            notice0['team_source_name'] = notice.team_source.name
        if notice.message_source is not None:
            message0 = recu_message(notice.message_source, user, 2)
            if message0 is False:
                message0 = None
            notice0['message'] = message0

        data["unread_notice_list"].append(notice0)
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': data})


def delete_notice(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    notice_id_list = body.get('notice_id_list')
    if notice_id_list is None or notice_id_list == []:
        return JsonResponse({'errno': 1003, 'errmsg': '消息id列表不能为空'})
    for notice_id in notice_id_list:
        if not Notice.objects.filter(id=notice_id).exists():
            return JsonResponse({'errno': 1004, 'errmsg': '消息id不存在'})
        notice = Notice.objects.get(id=notice_id)
        if notice.receiver != user:
            return JsonResponse({'errno': 1005, 'errmsg': '用户没有权限'})
        try:
            notice.delete()
        except:
            return JsonResponse({'errno': 1006, 'errmsg': '删除失败'})
    return JsonResponse({'errno': 0, 'errmsg': '删除成功'})
