import json

from django.utils import timezone

from Agile_models.models import *
from django.http import JsonResponse
from django.shortcuts import render


# Create your views here.

def get_all_pages(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token((body.get('token')))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误'})
    project_id = body.get('project_id')
    if project_id is None or (not Project.objects.filter(id=project_id).exists()):
        return JsonResponse({'errno': 1003, 'errmsg': 'project_id错误'})
    project = Project.objects.get(id=project_id)
    team = project.team
    if not Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不在该团队'})
    data = {}
    data['pages1'] = []
    data['pages2'] = []
    if not Prototype_pages.objects.filter(project=project).exists():
        return JsonResponse({'errno': 0, 'errmsg': '返回成功', 'data': data})
    pages = Prototype_pages.objects.filter(project=project).all()
    for page in pages:
        if page.editor.avatar.name is None or page.editor.avatar.name == "":
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL+page.editor.avatar.url
        if page.editor.avatar.name is None or page.editor.avatar.name == "":
            avatar_url2 = None
        else:
            avatar_url2 = settings.BACKEND_URL+page.editor.avatar.url
        if Team2User.objects.filter(user=page.creator,
                                    team=page.project.team):
            nick_name = Team2User.objects.get(user=page.creator,
                                              team=page.project.team).nickname
        else:
            nick_name = page.creator.username
        if Team2User.objects.filter(user=page.editor,
                                    team=page.project.team):
            nick_name2 = Team2User.objects.get(user=page.editor,
                                               team=page.project.team).nickname
        else:
            nick_name2 = page.editor.username
        if page.type == 1:
            data['pages1'].append({
            'id': page.id,
            'name': page.name,
            'type': page.type,
            'introduction': page.introduction,
            'creator_id': page.creator.id,
            'creator_name': nick_name,
            'creator_username': page.creator.username,
            'create_time': page.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            'creator_avatar' : avatar_url2,
            'editor_id': page.editor.id,
            'editor_name': nick_name2,
            'editor_username': page.editor.username,
            'editor_avatar':avatar_url,
            'edit_time': page.edit_time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        else:
            data['pages2'].append({
            'id': page.id,
            'name': page.name,
            'type': page.type,
            'introduction': page.introduction,
            'creator_id': page.creator.id,
            'creator_name': nick_name,
            'creator_username': page.creator.username,
            'create_time': page.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            'creator_avatar' : avatar_url2,
            'editor_id': page.editor.id,
            'editor_name': nick_name2,
            'editor_username': page.editor.username,
            'editor_avatar':avatar_url,
            'edit_time': page.edit_time.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return JsonResponse({'errno': 0, 'errmsg': '返回成功', 'data': data})


def create_page(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token((body.get('token')))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误'})
    project_id = body.get('project_id')
    if project_id is None or (not Project.objects.filter(id=project_id).exists()):
        return JsonResponse({'errno': 1003, 'errmsg': 'project_id错误'})
    project = Project.objects.get(id=project_id)
    team = project.team
    if not Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不在该团队'})
    name = body.get('name')
    if name is None:
        return JsonResponse({'errno': 1005, 'errmsg': 'name错误'})
    introduction = body.get('introduction')
    type0 = body.get('type')
    if type0 is None:
        return JsonResponse({'errno': 1006, 'errmsg': 'type错误'})
    page = Prototype_pages.objects.create(name=name,
                                          type = type0,
                                          introduction=introduction,
                                          project=project,
                                          creator=user,
                                          editor=user,
                                          create_time=timezone.now(),
                                          edit_time=timezone.now(),
                                          content='')
    page.save()
    project.edit_time = timezone.now()
    project.editor = user
    project.save()
    if page.editor.avatar.name is None or page.editor.avatar.name == "":
        avatar_url = None
    else:
        avatar_url = settings.BACKEND_URL+page.editor.avatar.url
    if page.editor.avatar.name is None or page.editor.avatar.name == "":
        avatar_url2 = None
    else:
        avatar_url2 = settings.BACKEND_URL+page.editor.avatar.url
    if Team2User.objects.filter(user=page.creator,
                                team=page.project.team):
        nick_name = Team2User.objects.get(user=page.creator,
                                          team=page.project.team).nickname
    else:
        nick_name = page.creator.username
    if Team2User.objects.filter(user=page.editor,
                                team=page.project.team):
        nick_name2 = Team2User.objects.get(user=page.editor,
                                           team=page.project.team).nickname
    else:
        nick_name2 = page.editor.username
    data = {
        'page_id': page.id,
        'name': page.name,
        'type': page.type,
        'introduction': page.introduction,
        'creator_id': page.creator.id,
        'creator_name': nick_name,
        'creator_username': page.creator.username,
        'create_time': page.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        'creator_avatar' : avatar_url2,
        'editor_id': page.editor.id,
        'editor_name': nick_name2,
        'editor_username': page.editor.username,
        'editor_avatar':avatar_url,
        'edit_time': page.edit_time.strftime("%Y-%m-%d %H:%M:%S"),
        'content': {},
    }
    return JsonResponse({'errno': 0, 'errmsg': '返回成功', 'data': data})


def edit_page(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token((body.get('token')))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误'})
    page_id = body.get('page_id')
    if page_id is None or (not Prototype_pages.objects.filter(id=page_id).exists()):
        return JsonResponse({'errno': 1003, 'errmsg': 'page_id错误'})
    page = Prototype_pages.objects.get(id=page_id)
    team = page.project.team
    if not Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不在该团队'})
    name = body.get('name')
    introduction = body.get('introduction')
    type0 = body.get('type')
    if name is not None:
        page.name = name
    if introduction is not None:
        page.introduction = introduction
    if type0 is not None:
        page.type = type0
    page.editor = user
    page.edit_time = timezone.now()
    page.save()
    page.project.edit_time = timezone.now()
    page.project.editor = user
    page.project.save()
    return JsonResponse({'errno': 0, 'errmsg': '返回成功'})


def delete_page(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token((body.get('token')))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误'})
    page_id = body.get('page_id')
    if page_id is None or (not Prototype_pages.objects.filter(id=page_id).exists()):
        return JsonResponse({'errno': 1003, 'errmsg': 'page_id错误'})
    page = Prototype_pages.objects.get(id=page_id)
    team = page.project.team
    if not Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不在该团队'})
    page.delete()
    page.project.edit_time = timezone.now()
    page.project.editor = user
    page.project.save()
    return JsonResponse({'errno': 0, 'errmsg': '返回成功'})


def get_page_content(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token((body.get('token')))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误'})
    page_id = body.get('page_id')
    if page_id is None or (not Prototype_pages.objects.filter(id=page_id).exists()):
        return JsonResponse({'errno': 1003, 'errmsg': 'page_id错误'})
    page = Prototype_pages.objects.get(id=page_id)
    team = page.project.team
    if not Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不在该团队'})
    data = {}
    data['content'] = page.content
    data['type'] = page.type
    return JsonResponse({'errno': 0, 'errmsg': '返回成功', 'data': data})


def save_page_content(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    user = auth_token((body.get('token')))
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误'})
    page_id = body.get('page_id')
    if page_id is None or (not Prototype_pages.objects.filter(id=page_id).exists()):
        return JsonResponse({'errno': 1003, 'errmsg': 'page_id错误'})
    page = Prototype_pages.objects.get(id=page_id)
    team = page.project.team
    if not Team2User.objects.filter(team=team, user=user, status__gt=-1).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '用户不在该团队'})
    content = body.get('content')
    if content is None:
        return JsonResponse({'errno': 1005, 'errmsg': 'content错误'})
    type0 = body.get('type')
    if type0 is None:
        return JsonResponse({'errno': 1006, 'errmsg': 'type错误'})
    page.content = content
    page.type = type0
    page.editor = user
    page.edit_time = timezone.now()
    page.save()
    page.project.edit_time = timezone.now()
    page.project.editor = user
    page.project.save()
    return JsonResponse({'errno': 0, 'errmsg': '返回成功'})
