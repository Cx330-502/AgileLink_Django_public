import json
import random
import re

import base64
import json
import os
import urllib.parse
from datetime import datetime

from django.conf import settings
import base64
import re
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import validate_email
from django.views.decorators.csrf import csrf_exempt
from Notice_center.consumers import *
from Public_chat.consumers import *
from Agile_models.models import *
from django.http import JsonResponse
import Team_manage.extra_codes.captcha as captchaclass
import json


# Create your views here.


def encrypt(data):
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


def decrypt(data):
    return base64.b64decode(data.encode('utf-8')).decode('utf-8')


def captcha(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    receiver_email = body.get("email")
    try:
        validate_email(receiver_email)
    except ValidationError:
        return JsonResponse({'errno': 1002, 'errmsg': '邮箱不符合规范'})
    verification = captchaclass.SendEmail(data=captchaclass.data,
                                          receiver=receiver_email).send_email()
    verification = encrypt(verification)
    data = {"verification": verification}
    return JsonResponse({'errno': 0, 'errmsg': '验证码发送成功', 'data': data})


def user_register(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    username = body.get("username")
    password = body.get("password")
    email = body.get("email")
    name = body.get("name")
    if username is None:
        return JsonResponse({'errno': 1002, 'errmsg': '用户名不能为空'})
    if password is None:
        return JsonResponse({'errno': 1003, 'errmsg': '密码不能为空'})
    if email is None:
        return JsonResponse({'errno': 1004, 'errmsg': '邮箱不能为空'})
    if not re.match(r"^[a-zA-Z0-9\u4e00-\u9fa5_-]{2,16}$", username):
        return JsonResponse({'errno': 1005, 'errmsg': '用户名不符合规范'})
    if not re.match(r"^[a-zA-Z0-9_-]{6,16}$", password):
        return JsonResponse({'errno': 1006, 'errmsg': '密码不符合规范'})
    if name is None:
        return JsonResponse({'errno': 1007, 'errmsg': '真实姓名不能为空'})
    if User.objects.filter(username=username).exists():
        return JsonResponse({'errno': 1007, 'errmsg': '用户名已存在'})
    if User.objects.filter(email=email).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '邮箱已存在'})
    user = User(username=username, password=password, email=email, name=name)
    user.save()
    if user.avatar.name == "" or user.avatar.name is None:
        ran_num = random.randint(1, 6)
        path = settings.MEDIA_ROOT + '/avatar/' + 'default/' + str(ran_num) + '.jpg'
        with open(path, 'rb') as f:
            user.avatar = File(f)
            user.save()
    return JsonResponse({'errno': 0, 'errmsg': '注册成功', 'data': {
        'user_id': user.id,
        'username': user.username,
        'name': user.name,
        'email': user.email,
        'avatar_url': settings.BACKEND_URL + user.avatar.url
    }})


def user_login(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    username = body.get("username")
    password = body.get("password")
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
    elif User.objects.filter(email=username).exists():
        user = User.objects.get(email=username)
    else:
        return JsonResponse({'errno': 1002, 'errmsg': '用户名或邮箱不存在'})
    if user.password == password:
        token = user.create_token(3600 * 24)
        avatar_url = None
        if user.avatar and user.avatar.name:
            avatar_url = settings.BACKEND_URL + user.avatar.url
        user.login_times = user.login_times + 1
        user.save()
        data = {'token': token,
                'user_id': user.id,
                'username': user.username,
                'name': user.name,
                'avatar': avatar_url,
                'email': user.email,
                'introduction': user.introduction,
                'login_times': user.login_times}
        return JsonResponse(
            {'errno': 0, 'errmsg': '登录成功', 'data': data})
    return JsonResponse({'errno': 1003, 'errmsg': '密码错误'})


def upload_avatar(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = request.POST.copy()
    user = auth_token(body.get("token"))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': '登录错误'})
    uploaded_avatar = request.FILES.get("avatar")
    if uploaded_avatar is None:
        return JsonResponse({'errno': 1003, 'errmsg': '文件为空' + str(user.username)})
    if uploaded_avatar.name is None or uploaded_avatar.name == '':
        return JsonResponse({'errno': 1004, 'errmsg': '文件为空' + str(user.username)})
    user.avatar = uploaded_avatar
    user.save()
    data = {"avatar": settings.BACKEND_URL + user.avatar.url}
    return JsonResponse({'errno': 0, 'errmsg': '保存成功', 'data': data})
    # body = request.POST.copy()
    # avatar_list = [request.FILES.get("avatar1"), request.FILES.get("avatar2"),
    #                request.FILES.get("avatar3"), request.FILES.get("avatar4"),
    #                request.FILES.get("avatar5"), request.FILES.get("avatar6")]
    # user_list = User.objects.all()
    # i = 0
    # return_list = []
    # for user in user_list:
    #     user.avatar = avatar_list[i]
    #     user.save()
    #     i += 1
    #     if i>=6:
    #         i = 0
    #     return_list.append({"user_id":user.id,
    #                         "username":user.username,
    #                         "avatar":settings.BACKEND_URL + user.avatar.url})
    # return JsonResponse({'errno': 0, 'errmsg': '保存成功', 'data': return_list})


def get_avatar(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user_ids = body.get("user_ids")
    if user_ids is None or user_ids == []:
        return JsonResponse({'errno': 1002, 'errmsg': '用户id不能为空'})
    return_list = []
    for user_id in user_ids:
        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({'errno': 1003, 'errmsg': '用户不存在'})
        user = User.objects.get(id=user_id)
        if user.avatar.name is None or user.avatar.name == '':
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + user.avatar.url
        user_info = {"user_id": user_id,
                     "avatar": avatar_url}
        return_list.append(user_info)
    return JsonResponse({'errno': 0, 'errmsg': '获取成功', 'data': {'avatars': return_list}})


def change_info(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get("token")
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': '登录错误'})
    username = body.get("username")
    name = body.get("name")
    introduction = body.get("introduction")
    if username is not None and username != "" and username != user.username:
        if User.objects.filter(username=username).exists():
            return JsonResponse({'errno': 1003, 'errmsg': '用户名已存在'})
        user.username = username
    if name is not None and name != "":
        user.name = name
    if introduction is not None:
        user.introduction = introduction
    user.save()
    data = {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "introduction": user.introduction,
        "email": user.email
    }
    return JsonResponse({'errno': 0, 'errmsg': '修改成功', 'data': data})


def change_password(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get("token")
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': '登录错误'})
    password = body.get("password")
    if password is None or password == "":
        return JsonResponse({'errno': 1003, 'errmsg': '密码不能为空'})
    if not re.match(r"^[a-zA-Z0-9_-]{6,16}$", password):
        return JsonResponse({'errno': 1004, 'errmsg': '密码不符合规范'})
    user.password = password
    user.save()
    return JsonResponse({'errno': 0, 'errmsg': '修改成功'})


def change_email(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get("token")
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': '登录错误'})
    email = body.get("email")
    if email is None or email == "":
        return JsonResponse({'errno': 1003, 'errmsg': '邮箱不能为空'})
    user.email = email
    user.save()
    return JsonResponse({'errno': 0, 'errmsg': '修改成功'})


def file_receive(request):
    if request.method != "POST":
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = request.POST.copy()
    user = auth_token(body.get("token"))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': '登录错误'})
    uploaded_file = request.FILES.get("file")
    if uploaded_file is None:
        return JsonResponse({'errno': 1003, 'errmsg': '文件为空'})
    save_path = settings.MEDIA_ROOT + "/temp/"
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, uploaded_file.name)
    while os.path.exists(file_path):
        file_path = file_path.split(".")[0] + "_1." + file_path.split(".")[1]
    file_name = file_path.split("/")[-1]
    with open(file_path, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    url = settings.BACKEND_URL + '/media/' + "temp/" + file_name
    data = {"url": url}
    data = {"url": url}
    return JsonResponse({'errno': 0, 'errmsg': '保存成功', 'data': data})


def create_team(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    name = body.get('name')
    introduction = body.get('introduction')
    creator = user
    nickname = body.get('nickname')
    team = Team.objects.filter(name=name)
    if team.exists():
        return JsonResponse({'errno': 1003, 'errmsg': '已经存在此名称的团队'})
    else:
        new_team = Team(name=name, introduction=introduction, creator=creator)
        new_team.save()
        new_team2user = Team2User(team=new_team, user=user, nickname=nickname, status=3)
        new_team2user.save()
        if user.avatar.name is None or user.avatar.name == '':
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + user.avatar.url
        data = {
            'team_id': new_team.id,
            'team_name': new_team.name,
            'introduction': new_team.introduction,
            'creator_id': new_team.creator.id,
            'creator_name': new_team.creator.username,
            'creator_avatar': avatar_url,
            'nickname': new_team2user.nickname
        }
        return JsonResponse({'errno': 0, 'errmsg': '创建团队成功', 'data': data})


# 生成链接
def generate_team_link(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个团队'})
    try:
        team2user = Team2User.objects.get(team=team, user=user)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '您还不在团队中,无法邀请其他用户'})
    if team2user.status <= 1:
        return JsonResponse({'errno': 1005, 'errmsg': '没有使用邀请链接的权限'})
    else:
        team_link = team.generate_link()
    return JsonResponse({'errno': 0, 'errmsg': '生成邀请链接成功', 'data': team_link})


# 通过用户名邀请用户
def invite_member(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个团队'})
    invitee_name = body.get('invitee_name')
    try:
        invitee = User.objects.get(username=invitee_name)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '被邀请用户不存在'})
    try:
        inviter2team = Team2User.objects.get(team=team, user=user)
    except Exception as e:
        return JsonResponse({'errno': 1005, 'errmsg': '您还不在这个团队中'})
    if Team2User.objects.filter(team=team, user=invitee).exists():
        invitee2team = Team2User.objects.get(team=team, user=invitee)
        if (invitee2team.status == 1 or inviter2team.status == 2 or
                inviter2team.status == 3):
            return JsonResponse({'errno': 1006, 'errmsg': '您想要邀请的成员已经在团队中了'})
        elif invitee2team.status == -1:
            return JsonResponse({'errno': 1007, 'errmsg': '您已经向对方发送过邀请了,请您耐心等待'})
    if inviter2team.status < 2 or inviter2team.status > 3:
        return JsonResponse({'errno': 1008, 'errmsg': '您的权限有问题'})
    invite_content = '%s团队的%s邀请您加入对方团队' % (team.name, user.username)
    invite_notice = Notice(type=1, content=invite_content, sender=user,
                           receiver=invitee, send_time=datetime.now(),
                           read_status=1, team_source=team)
    invite_notice.save()
    if invitee.avatar.name is None or invitee.avatar.name == '':
        invitee_avatar_url = None
    else:
        invitee_avatar_url = settings.BACKEND_URL + invitee.avatar.url
    if user.avatar.name is None or user.avatar.name == '':
        inviter_avatar_url = None
    else:
        inviter_avatar_url = settings.BACKEND_URL + user.avatar.url
    data = {
        "type": 1,
        "invitee_id": invitee.id,
        "invitee_name": invitee.username,
        "invitee_avatar": invitee_avatar_url,
        "inviter_id": user.id,
        "inviter_name": user.username,
        "inviter_avatar": inviter_avatar_url,
        "team_id": team.id,
        "team_name": team.name,
        "content": invite_content,  # "邀请您加入对方团队
        "notice_id": invite_notice.id,
    }
    try:
        USER_DICT2[invitee.id].send(text_data=json.dumps(data))
    except:
        pass
    new_team2user = Team2User(team=team, user=invitee, status=-1)
    new_team2user.save()
    return JsonResponse({'errno': 0, 'errmsg': '向%s的加入团队邀请发送成功' % invitee.username,
                         'data': data})


# 被邀请人处理加入申请
def invitee_handle_invitation(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if_agree = body.get('if_agree')  # 1 代表同意加入 -1 代表拒绝加入
    if team_id is None:
        return JsonResponse({'errno': 1003, 'errmsg': '团队id不能为空'})
    if not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '团队不存在'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1005, 'errmsg': '获取团队出错'})
    if not Team2User.objects.filter(team=team, user=user).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '您没有收到邀请'})
    try:
        team2invitee = Team2User.objects.get(team=team, user=user)
    except Exception as e:
        return JsonResponse({'errno': 1007, 'errmsg': '获取邀请出错'})
    try:
        invitation_notice = Notice.objects.get(type=1, receiver=user,
                                               team_source=team, read_status=1)
    except Exception as e:
        return JsonResponse({'errno': 1008, 'errmsg': str(e), 'data': {
            'type': 1,
            'invitee_id': user.id,
            'invitee_name': user.username,
            'team_id': team.id,
            'read_status': 1
        }})
    invitation_sender = invitation_notice.sender
    invitation_notice.read_status = -1
    invitation_notice.save()
    notice_info = ''
    if if_agree == 1:
        team2invitee.status = 1
        nickname = body.get('nickname')
        team2invitee.nickname = nickname
        team2invitee.save()
        notice_info = '%s已经加入了您的团队%s' % (user.username, team.name)
        try:
            room_name = f"t{team.id}"
            (async_to_sync(USER_DICT[user.id].channel_layer.group_add)
             (room_name, USER_DICT[user.id].channel_name))
            print("6 > 客户端成功加入聊天服务端" + room_name)
        except Exception as e:
            print("6 > 客户端加入聊天服务端失败" + room_name)
            print(e)
    elif if_agree == -1:
        team2invitee.delete()
        notice_info = '%s已经拒绝了加入您的团队%s' % (user.username, team.name)
    new_notice = Notice(type=2, content=notice_info, sender=user,
                        receiver=invitation_sender, send_time=datetime.now(),
                        read_status=1)
    new_notice.save()
    if invitation_sender.avatar.name is None or invitation_sender.avatar.name == '':
        invitation_sender_avatar_url = None
    else:
        invitation_sender_avatar_url = settings.BACKEND_URL + invitation_sender.avatar.url
    if user.avatar.name is None or user.avatar.name == '':
        invitee_avatar_url = None
    else:
        invitee_avatar_url = settings.BACKEND_URL + user.avatar.url
    data = {
        "type": 2,
        "invitee_id": user.id,
        "invitee_name": user.username,
        "invitee_avatar": invitee_avatar_url,
        "inviter_id": invitation_sender.id,
        "inviter_name": invitation_sender.username,
        "inviter_avatar": invitation_sender_avatar_url,
        "team_id": team.id,
        "team_name": team.name,
        "content": notice_info,  # "已经加入了您的团队
        "notice_id": new_notice.id,
    }
    try:
        USER_DICT2[invitation_sender.id].send(text_data=json.dumps(data))
    except:
        pass
    return JsonResponse({'errno': 0, 'errmsg': '处理邀请', 'data': data})


def apply_join_team(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None:
        return JsonResponse({'errno': 1003, 'errmsg': '团队id不能为空'})
    if not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '团队不存在'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1005, 'errmsg': '获取团队出错'})
    if Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '您已经在团队中'})
    if Team2User.objects.filter(team=team, user=user, status=-1).exists():
        return JsonResponse({'errno': 1007, 'errmsg': '您已经向该团队发送过申请了,请您耐心等待'})
    new_team2user = Team2User(team=team, user=user, status=-1)
    new_team2user.save()
    if user.avatar.name is None or user.avatar.name == '':
        invitee_avatar_url = None
    else:
        invitee_avatar_url = settings.BACKEND_URL + user.avatar.url
    manager_list = Team2User.objects.filter(team=team, status__gt=1)
    for manager in manager_list:
        manager_user = manager.user
        if manager_user.avatar.name is None or manager_user.avatar.name == '':
            manager_avatar_url = None
        else:
            manager_avatar_url = settings.BACKEND_URL + manager_user.avatar.url
        notice = Notice(type=3, content='%s申请加入您的团队%s' % (user.username, team.name), sender=user,
                        receiver=manager_user, send_time=datetime.now(),
                        read_status=1)
        notice.save()
        data = {
            "type": 3,
            "invitee_id": user.id,
            "invitee_name": user.username,
            "invitee_avatar": invitee_avatar_url,
            "manager_id": manager_user.id,
            "manager_name": manager_user.username,
            "manager_avatar": manager_avatar_url,
            "team_id": team.id,
            "team_name": team.name,
            "content": "%s申请加入您的团队%s" % (user.username, team.name),  # "已经加入了您的团队
            "notice_id": notice.id,
        }
        try:
            USER_DICT2[manager_user.id].send(text_data=json.dumps(data))
        except:
            pass

    return JsonResponse({'errno': 0, 'errmsg': '申请成功'})


def applicant_handle_application(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    notice_id = body.get('notice_id')
    if notice_id is None:
        return JsonResponse({'errno': 1003, 'errmsg': '通知id不能为空'})
    if not Notice.objects.filter(id=notice_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '通知不存在'})
    notice = Notice.objects.get(id=notice_id)
    if notice.type != 3:
        return JsonResponse({'errno': 1005, 'errmsg': '通知类型错误'})
    if notice.receiver != user:
        return JsonResponse({'errno': 1006, 'errmsg': '您没有权限处理该通知'})
    if_agree = body.get('if_agree')  # 1 代表同意加入 0 代表拒绝加入
    if if_agree is None:
        return JsonResponse({'errno': 1007, 'errmsg': '处理结果不能为空'})
    team_id = body.get('team_id')
    if team_id is None or not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '团队不存在'})
    team = Team.objects.get(id=team_id)
    if if_agree == 1:
        if (Team2User.objects.filter(team=team, user=notice.sender, status=-1).exists()):
            team2user = Team2User.objects.get(team=team, user=notice.sender, status=-1)
            team2user.status = 1
            team2user.save()
        elif Team2User.objects.filter(team=team, user=notice.sender, status__gt=0).exists():
            return JsonResponse({'errno': 1009, 'errmsg': '该用户已经在团队中'})
        else:
            team2user = Team2User(team=team, user=user, status=1)
            team2user.save()
        notice1 = Notice(type=4, content='您已经加入%s团队' % (team.name), sender=user,
                         receiver=notice.sender, send_time=datetime.now(),
                         read_status=1)
        notice.read_status = -1
        notice.save()
        notice1.save()
        try:
            room_name = f"t{team.id}"
            (async_to_sync(USER_DICT[notice.sender.id].channel_layer.group_add)
             (room_name, USER_DICT[notice.sender.id].channel_name))
            print("6 > 客户端成功加入聊天服务端" + room_name)
        except Exception as e:
            print("6 > 客户端加入聊天服务端失败")
            print(e)
        if user.avatar.name is None or user.avatar.name == '':
            manager_avatar_url = None
        else:
            manager_avatar_url = settings.BACKEND_URL + user.avatar.url
        if notice.sender.avatar.name is None or notice.sender.avatar.name == '':
            invitee_avatar_url = None
        else:
            invitee_avatar_url = settings.BACKEND_URL + notice.sender.avatar.url
        data = {
            "type": 4,
            "invitee_id": notice.sender.id,
            "invitee_name": notice.sender.username,
            "invitee_avatar": invitee_avatar_url,
            "manager_id": user.id,
            "manager_name": user.username,
            "manager_avatar": manager_avatar_url,
            "team_id": team.id,
            "team_name": team.name,
            "content": "您已经加入%s团队" % (team.name),  # "已经加入了您的团队
            "notice_id": notice1.id,
        }
        try:
            USER_DICT2[notice.sender.id].send(text_data=json.dumps(data))
        except:
            pass
        return JsonResponse({'errno': 0, 'errmsg': '处理成功'})
    elif if_agree == -1:
        notice.read_status = -1
        if Team2User.objects.filter(team=team, user=notice.sender,
                                    status=-1).exists():
            team2user = Team2User.objects.get(team=team, user=notice.sender,
                                              status=-1)
            team2user.delete()
        elif team2user := Team2User.objects.filter(team=team, user=notice.sender,
                                                   status__gt=0).exists():
            return JsonResponse({'errno': 1010, 'errmsg': '该用户已经在团队中'})
        notice.save()
        notice1 = Notice(type=4, content='您已经拒绝%s加入%s团队' % (notice.sender, team.name),
                         sender=notice.sender, receiver=user,
                         send_time=datetime.now(), read_status=1)
        notice1.save()
        if user.avatar.name is None or user.avatar.name == '':
            manager_avatar_url = None
        else:
            manager_avatar_url = settings.BACKEND_URL + user.avatar.url
        if notice.sender.avatar.name is None or notice.sender.avatar.name == '':
            invitee_avatar_url = None
        else:
            invitee_avatar_url = settings.BACKEND_URL + notice.sender.avatar.url
        data = {
            "type": 4,
            "invitee_id": notice.sender.id,
            "invitee_name": notice.sender.username,
            "invitee_avatar": invitee_avatar_url,
            "manager_id": user.id,
            "manager_name": user.username,
            "manager_avatar": manager_avatar_url,
            "team_id": team.id,
            "team_name": team.name,
            "content": "您已经被拒绝加入%s团队" % (team.name),  # "已经加入了您的团队
            "notice_id": notice1.id,
        }
        try:
            USER_DICT2[notice.sender.id].send(text_data=json.dumps(data))
        except:
            pass
        return JsonResponse({'errno': 0, 'errmsg': '处理成功'})


def delete_member(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    delete_user_id = body.get('delete_user_id')
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在该团队'})
    try:
        delete_user = User.objects.get(id=delete_user_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '不存在该用户'})
    try:
        team2user = Team2User.objects.get(team=team, user=user)
        team2delete_user = Team2User.objects.get(team=team, user=delete_user)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '团队中不存在该用户'})
    if team2user.status == 3 or (team2user.status == 2 and team2delete_user.status == 1):
        Team2User.delete(team2delete_user)
        notice = Notice(type=7, content='您已经被移出%s团队' % (team.name), sender=user,
                        receiver=delete_user, send_time=datetime.now(),
                        read_status=1)
        notice.save()
        if user.avatar.name is None or user.avatar.name == '':
            manager_avatar_url = None
        else:
            manager_avatar_url = settings.BACKEND_URL + user.avatar.url
        if delete_user.avatar.name is None or delete_user.avatar.name == '':
            invitee_avatar_url = None
        else:
            invitee_avatar_url = settings.BACKEND_URL + delete_user.avatar.url
        data = {
            "type": 7,
            "sender_id": user.id,
            "sender_name": user.username,
            "sender_avatar": manager_avatar_url,
            "receiver_id": delete_user.id,
            "receiver_name": delete_user.username,
            "receiver_avatar": invitee_avatar_url,
            "team_id": team.id,
            "team_name": team.name,
            "content": "您已经被移出%s团队" % (team.name),  # "已经加入了您的团队
            "notice_id": notice.id,
        }
        try:
            USER_DICT2[delete_user.id].send(text_data=json.dumps(data))
        except:
            pass
    else:
        return JsonResponse({'errno': 1005, 'errmsg': '您的权限不足'})
    try:
        room_name = f"t{team.id}"
        (async_to_sync(USER_DICT[delete_user.id].channel_layer.group_discard)
         (room_name, USER_DICT[delete_user.id].channel_name))
        print("6 > 客户端成功退出聊天服务端" + room_name)
    except Exception as e:
        print("6 > 客户端退出聊天服务端失败")
        print(e)
    return JsonResponse({'errno': 0, 'errmsg': '删除成功'})


def grant_admin(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    granted_user_id = body.get('granted_user_id')
    if granted_user_id is None:
        return JsonResponse({'errno': 1003, 'errmsg': '用户id不能为空'})
    if not User.objects.filter(id=granted_user_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不存在'})
    granted_user = User.objects.get(id=granted_user_id)
    team_id = body.get('team_id')
    if team_id is None:
        return JsonResponse({'errno': 1005, 'errmsg': '团队id不能为空'})
    if not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '团队不存在'})
    team = Team.objects.get(id=team_id)
    if not Team2User.objects.filter(team=team, user=user, status__gt=1).exists():
        return JsonResponse({'errno': 1009, 'errmsg': '您没有权限'})
    if not Team2User.objects.filter(team=team, user=granted_user, status=1).exists():
        return JsonResponse({'errno': 1010, 'errmsg': '该用户不是普通成员'})
    team2user = Team2User.objects.get(team=team, user=granted_user)
    team2user.status = 2
    team2user.save()
    notice = Notice(type=5, content='您已经被授予%s团队管理员权限' % (team.name), sender=user,
                    receiver=granted_user, send_time=datetime.now(),
                    read_status=1)
    notice.save()
    if user.avatar.name is None or user.avatar.name == '':
        avatar_url1 = None
    else:
        avatar_url1 = settings.BACKEND_URL + user.avatar.url
    if granted_user.avatar.name is None or granted_user.avatar.name == '':
        avatar_url2 = None
    else:
        avatar_url2 = settings.BACKEND_URL + granted_user.avatar.url
    data = {
        "type": 5,
        "sender_id": user.id,
        "sender_name": user.username,
        "sender_avatar": avatar_url1,
        "receiver_id": granted_user.id,
        "receiver_name": granted_user.username,
        "receiver_avatar": avatar_url2,
        "team_id": team.id,
        "team_name": team.name,
        "content": "您已经被授予%s团队管理员权限" % (team.name),  # "已经加入了您的团队
        "notice_id": notice.id,
    }
    try:
        USER_DICT2[granted_user.id].send(text_data=json.dumps(data))
    except:
        pass
    return JsonResponse({'errno': 0, 'errmsg': '授权成功'})


def dismiss_admin(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    granted_user_id = body.get('granted_user_id')
    if granted_user_id is None:
        return JsonResponse({'errno': 1003, 'errmsg': '用户id不能为空'})
    if not User.objects.filter(id=granted_user_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不存在'})
    granted_user = User.objects.get(id=granted_user_id)
    team_id = body.get('team_id')
    if team_id is None:
        return JsonResponse({'errno': 1005, 'errmsg': '团队id不能为空'})
    if not Team.objects.filter(id=team_id).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '团队不存在'})
    team = Team.objects.get(id=team_id)
    if not Team2User.objects.filter(team=team, user=user, status=3).exists():
        return JsonResponse({'errno': 1009, 'errmsg': '您没有权限'})
    if not Team2User.objects.filter(team=team, user=granted_user, status=2).exists():
        return JsonResponse({'errno': 1010, 'errmsg': '该用户不是管理员'})
    team2user = Team2User.objects.get(team=team, user=granted_user)
    team2user.status = 1
    team2user.save()
    notice = Notice(type=6, content='您已经被取消%s团队管理员权限' % (team.name), sender=user,
                    receiver=granted_user, send_time=datetime.now(),
                    read_status=1)
    notice.save()
    if user.avatar.name is None or user.avatar.name == '':
        avatar_url1 = None
    else:
        avatar_url1 = settings.BACKEND_URL + user.avatar.url
    if granted_user.avatar.name is None or granted_user.avatar.name == '':
        avatar_url2 = None
    else:
        avatar_url2 = settings.BACKEND_URL + granted_user.avatar.url
    data = {
        "type": 6,
        "sender_id": user.id,
        "sender_name": user.username,
        "sender_avatar": avatar_url1,
        "receiver_id": granted_user.id,
        "receiver_name": granted_user.username,
        "receiver_avatar": avatar_url2,
        "team_id": team.id,
        "team_name": team.name,
        "content": "您已经被取消%s团队管理员权限" % (team.name),  # "已经加入了您的团队
        "notice_id": notice.id,
    }
    try:
        USER_DICT2[granted_user.id].send(text_data=json.dumps(data))
    except:
        pass
    return JsonResponse({'errno': 0, 'errmsg': '取消授权成功'})


def view_member_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在该团队'})

    team2user = Team2User.objects.filter(team=team, status__gt=-1).order_by('-status')

    return_list = []

    for data in team2user:
        nickname = data.nickname
        user_in_team = data.user
        user_id = user_in_team.id
        username = user_in_team.username
        email = user_in_team.email
        name = user_in_team.name
        if user_in_team.avatar.name is None or user_in_team.avatar.name == '':
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + user_in_team.avatar.url
        status = ''
        if data.status == 1:
            status = '普通成员'
        elif data.status == 2:
            status = '管理员'
        elif data.status == 3:
            status = '创建者'
        user_info = {
            "name": name,
            "user_id": user_id,
            "username": username,
            "email": email,
            "nickname": nickname,
            "status": status,
            "status_num": data.status,  # 1 普通成员 2 管理员 3 创建者
            "avatar": settings.BACKEND_URL + user_in_team.avatar.url
        }
        return_list.append(user_info)
    return JsonResponse({'errno': 0, 'errmsg': '显示成员信息成功', 'data': return_list})


def view_team_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    return_list = []
    user_teams = Team2User.objects.filter(user=user, status__gt=-1)
    # 用户已经拥有组织
    if user_teams.exists():
        for data in user_teams:
            team = data.team
            name = team.name
            introduction = team.introduction
            creator_name = team.creator.username
            creator_id = team.creator.id
            if team.creator.avatar.name is None or team.creator.avatar.name == '':
                creator_avatar_url = None
            else:
                creator_avatar_url = settings.BACKEND_URL + team.creator.avatar.url
            status = ''
            if data.status == 1:
                status = '普通成员'
            elif data.status == 2:
                status = '管理员'
            elif data.status == 3:
                status = '创建者'
            team_info = {
                "name": name,
                "team_id": team.id,
                "introdution": introduction,
                "creator_name": creator_name,
                "creator_id": creator_id,
                "creator_avatar": creator_avatar_url,
                "status": status,
                'status_num': data.status
            }
            return_list.append(team_info)
    return JsonResponse({'errno': 0, 'errmsg': '查看团队信息成功', 'data': return_list})


def edit_personal_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    reusername = body.get('reusername')
    reintroduction = body.get('reintroduction')
    if (reusername is None or reusername == "") and (reintroduction is None or reintroduction == ''):
        return JsonResponse({'errno': 1005, 'errmsg': '不合法的名称及简介'})
    if not (reusername is None or reusername == ''):
        if User.objects.filter(username=reusername).exists():
            return JsonResponse({'errno': 1006, 'errmsg': '您想要重新命名的用户名已被使用'})
        if user.username == reusername:
            return JsonResponse({'errno': 1007, 'errmsg': '您想要重新命名的用户名和当前的一致'})
        user.username = reusername
        user.save()
    if not (reintroduction is None or reintroduction == ''):
        user.introduction = reintroduction
        user.save()
    return JsonResponse({'errno': 0, 'errmsg': '编辑个人信息成功'})


def show_single_team_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入正确的团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '不存在这个团队'})
    if not Team2User.objects.filter(team=team, user=team.creator).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '创建者不存在?'})
    team2user = Team2User.objects.get(team=team, user=team.creator)
    if team.creator.avatar.name is None or team.creator.avatar.name == '':
        avatar_url = None
    else:
        avatar_url = settings.BACKEND_URL + team.creator.avatar.url
    data = {
        "team_id": team.id,
        "team_name": team.name,
        "team_introduction": team.introduction,
        "creator_name": team.creator.username,
        "creator_username": team.creator.username,
        "creator_id": team.creator.id,
        "creator_avatar": avatar_url,
        "creator_introduction": team.creator.introduction,
        "creator_nick_name": team2user.nickname,
        "creator_email": team.creator.email,
    }
    return JsonResponse({'errno': 0, 'errmsg': '查看团队id为%s的团队信息成功' % team_id, 'data': data})


def get_user_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)

    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    user_list = body.get('user_list')
    if user_list is None or user_list == '':
        return JsonResponse({'errno': 1005, 'errmsg': '请传入正确的用户列表'})
    return_list = []
    for user_id in user_list:
        if not User.objects.filter(id=user_id).exists():
            return JsonResponse({'errno': 1006, 'errmsg': '用户列表中存在不存在的用户'})
        user0 = User.objects.get(id=user_id)
        data = {
            "user_id": user0.id,
            "username": user0.username,
            "name": user0.name,
            "email": user0.email,
            "avatar": settings.BACKEND_URL + user0.avatar.url
        }
        return_list.append(data)
    return JsonResponse({'errno': 0, 'errmsg': '查看用户信息成功', 'data': return_list})
