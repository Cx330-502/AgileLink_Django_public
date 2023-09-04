import base64
import json
import os.path
import time

from django.conf import settings
from django.core.signing import Signer
from django.db import models
from django.core import signing
import jwt

team_url = 'http://127.0.0.1:3306/welcome_to_team/'
doc_readonly_url = 'http://127.0.0.1:3306/doc_readonly/'
doc_edit_url = 'http://127.0.0.1:3306/doc_edit/'

def encrypt(data):
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


def decrypt(data):
    return base64.b64decode(data.encode('utf-8')).decode('utf-8')

def auth_token(token):
    salt = settings.SECRET_KEY
    try:
        payload = jwt.decode(token, salt, algorithms=['HS256'], verify=True)
        exp_time = payload['exp']
        if time.time() > exp_time:
            raise Exception('Token has expired')
    except Exception as e:
        print(e)
        return False
    if User.objects.filter(id=payload['id']).exists():
        return User.objects.get(id=payload['id'])
    else:
        return False


def avatar_file_upload_to(instance, filename):
    filename = os.path.basename(filename)
    path = 'avatar/' + str(instance.id) + '/'
    os.makedirs(settings.MEDIA_ROOT + path, exist_ok=True)
    path = path + filename
    while os.path.exists(settings.MEDIA_ROOT + path):
        path = path.split(".")[0] + "_1." + path.split(".")[1]
    filename = path.split('/')[-1]
    return path


# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=20, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=20, verbose_name="密码")
    email = models.EmailField(max_length=254, unique=True, verbose_name="邮箱")
    name = models.CharField(max_length=20, verbose_name="姓名")
    introduction = models.CharField(max_length=100, verbose_name="简介", null=True)
    avatar = models.ImageField(upload_to=avatar_file_upload_to, verbose_name="头像", null=True)
    login_times = models.IntegerField(default=0, verbose_name="登录次数")
    def create_token(self, timeout):
        salt = settings.SECRET_KEY
        headers = {
            "typ": "jwt",
            "alg": "HS256"
        }
        payload = {'id': self.id, 'username': self.username, 'exp': time.time() + timeout}
        token = jwt.encode(payload=payload, key=salt, algorithm="HS256", headers=headers)
        return token


class Team(models.Model):
    name = models.CharField(max_length=20, verbose_name="团队名")
    introduction = models.CharField(max_length=100, verbose_name="简介", null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    link = models.CharField(max_length=100, null=True, verbose_name="团队链接")

    def generate_link(self):
        dict0 = {
            'id': self.id,
            'name': self.name,
            'introduction': self.introduction,
            'creator': self.creator.username,
        }
        value = encrypt(json.dumps(dict0))
        return team_url + value


def decode_team_link(link):
    value = link.spilt('/')[-1]
    try:
        team_id = Signer.unsign(value)
    except Exception as e:
        return False
    return team_url + team_id


class Team2User(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="团队")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    nickname = models.CharField(max_length=20, verbose_name="昵称")
    status = models.IntegerField(verbose_name="权限")
    #     1：普通成员 2：管理员 3：创建者 -1待审核加入
    exit_time = models.DateTimeField(verbose_name="退出群聊时间", auto_now=True)


#       退出群聊后所有聊天消息为未读消息

class Group_chat(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="团队")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    name = models.CharField(max_length=20, verbose_name="群聊名")
    introduction = models.CharField(max_length=100, verbose_name="简介", null=True)


class Group_chat2User(models.Model):
    group_chat = models.ForeignKey(Group_chat, on_delete=models.CASCADE, verbose_name="群聊")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    status = models.IntegerField(verbose_name="权限")
    #     1：普通成员 2：创建者
    exit_time = models.DateTimeField(verbose_name="退出群聊时间", auto_now=True)


def message_file_upload_to(instance, filename):
    filename = os.path.basename(filename)
    if instance.type == 1:
        room_name = f"t{instance.receive_team.id}"
    elif instance.type == 2:
        if instance.sender.id < instance.receive_user.id:
            room_name = f"u{instance.sender.id}u{instance.receive_user.id}"
        else:
            room_name = f"u{instance.receive_user.id}u{instance.sender.id}"
    elif instance.type == 3:
        room_name = f"g{instance.receive_group.id}"
    path = 'message/' + room_name + '/'
    os.makedirs(settings.MEDIA_ROOT + path, exist_ok=True)
    path = path + filename
    while os.path.exists(settings.MEDIA_ROOT + path):
        path = path.split(".")[0] + "_1." + path.split(".")[1]
    print (path)
    return path


class Message(models.Model):
    type = models.IntegerField(verbose_name="类型")
    # type =1 在群里发 2 在私聊发
    content = models.CharField(max_length=100, verbose_name="内容", null=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="发送者")
    receive_team = models.ForeignKey(Team, on_delete=models.CASCADE,
                                     verbose_name="接收团队", null=True,
                                     related_name="receive_team")
    receive_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                     verbose_name="接收用户", null=True,
                                     related_name="receive_user")
    receive_group = models.ForeignKey(Group_chat, on_delete=models.CASCADE,
                                      verbose_name="接收群聊", null=True,
                                      related_name="receive_group")
    send_time = models.DateTimeField(verbose_name="发送时间", auto_now_add=True)
    file_content = models.FileField(upload_to=message_file_upload_to,
                                    verbose_name="文件内容", null=True)
    read_status = models.IntegerField(verbose_name="阅读状态", default=0)
    message_source = models.TextField(verbose_name="消息来源", null=True)


#     0：未读 1：已读


class Project(models.Model):
    name = models.CharField(max_length=20, verbose_name="项目名")
    introduction = models.CharField(max_length=100, verbose_name="简介", null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者",
                                related_name="project_creator")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="团队",
                             related_name="project_team")
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    edit_time = models.DateTimeField(verbose_name="编辑时间", auto_now=True)
    editor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="编辑者",
                               null=True, related_name="project_editor")
    status = models.IntegerField(verbose_name="状态", default=1)


#     1：正常 -1：回收站

class Project2User(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="团队")
    star = models.IntegerField(verbose_name="收藏", default=0)
    #     0：未收藏 1：已收藏


class Prototype_pages(models.Model):
    name = models.CharField(max_length=20, verbose_name="页面名")
    type = models.IntegerField(verbose_name="类型")
    introduction = models.CharField(max_length=100, verbose_name="简介", null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目",
                                related_name="prototype_project")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者",
                                related_name="prototype_creator")
    editor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="编辑者",
                               null=True, related_name="prototype_editor")
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    edit_time = models.DateTimeField(verbose_name="编辑时间", auto_now=True)
    content = models.TextField(verbose_name="内容")



class Dictionary(models.Model):
    name = models.CharField(max_length=20, verbose_name="文件夹名")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目",
                                related_name="dictionary_project")
    parent_dict = models.ForeignKey('self', on_delete=models.CASCADE,
                                    verbose_name="父文件夹", null=True)


class Documents(models.Model):
    name = models.CharField(max_length=20, verbose_name="文档名")
    introduction = models.CharField(max_length=100, verbose_name="简介", null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目",
                                related_name="document_project")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者",
                                related_name="document_creator")
    editor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="编辑者", null=True,
                               related_name="document_editor")
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    edit_time = models.DateTimeField(verbose_name="编辑时间", auto_now=True)
    link_view = models.CharField(max_length=100, verbose_name="查看链接", null=True)
    link_edit = models.CharField(max_length=100, verbose_name="编辑链接", null=True)
    doc_dict = models.ForeignKey(Dictionary, on_delete=models.CASCADE, verbose_name="文件夹",
                                 related_name="document_dict", null=True)

    def generate_readonly_link(self):
        dict0 = {
            'id': self.id,
            'name': self.name,
            'introduction': self.introduction,
            'project': self.project.name,
            'creator': self.creator.username,
        }
        value = encrypt(json.dumps(dict0))
        return doc_readonly_url + value

    def generate_edit_link(self):
        dict0 = {
            'id': self.id,
            'name': self.name,
            'introduction': self.introduction,
            'project': self.project.name,
            'creator': self.creator.username,
        }
        value = encrypt(json.dumps(dict0))
        return doc_edit_url + value


class Document_history(models.Model):
    document = models.ForeignKey(Documents, on_delete=models.CASCADE, verbose_name="文档",
                                 related_name="document_history_document")
    editor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="编辑者",
                               related_name="document_history_editor")
    edit_time = models.DateTimeField(verbose_name="编辑时间", auto_now=True)
    content = models.TextField(verbose_name="内容")


class Notice(models.Model):
    # 1:团队创建者或管理员向其他用户发送邀请 2:其他用户向团队创建者或管理员发送通知
    # 1 被邀请  2 对方是否同意邀请 3 收到申请 4 申请是否通过
    # 5 升级 6 降级 7 踢出
    # 8 群聊被艾特 9 群聊被艾特全体
    # 10 文档被艾特
    # 11 群聊被邀请 12群聊被艾特 13 群聊被艾特全体 14 群聊解散 15 群聊退出通知
    type = models.IntegerField(verbose_name="类型")
    content = models.CharField(max_length=100, verbose_name="内容")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="发送者",
                               related_name="notice_sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="接收者",
                                 related_name="notice_receiver")
    doc_source = models.ForeignKey(Documents, on_delete=models.CASCADE, verbose_name="文档来源",
                                   null=True, related_name="notice_doc_source")
    team_source = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="团队来源",
                                    null=True, related_name="notice_team_source")
    group_chat_source = models.ForeignKey(Group_chat, on_delete=models.CASCADE,
                                          verbose_name="群聊来源", null=True,
                                          related_name="notice_group_chat_source")
    message_source = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="消息来源",
                                       null=True, related_name="notice_message_source")
    send_time = models.DateTimeField(verbose_name="发送时间", auto_now_add=True)
    read_status = models.IntegerField(verbose_name="阅读状态", default=1)
#     1：未读 -1：已读
