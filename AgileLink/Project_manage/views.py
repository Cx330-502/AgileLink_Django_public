import json

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from Agile_models.models import *


def create_project(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    name = body.get('name')
    introduction = body.get('introduction')
    team_id = body.get('team_id')
    if name is None or name == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入合法的名称'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    project = Project.objects.filter(name=name)
    if project.exists():
        return JsonResponse({'errno': 1005, 'errmsg': '本团队已经有这个名称的项目了'})
    else:
        creator = user
        editor = user
        new_project = Project(name=name, introduction=introduction, creator=creator, team=team, editor=editor)
        new_project.save()
        new_dictionary_name = name
        new_dictionary = Dictionary(name=new_dictionary_name, project=new_project)
        new_dictionary.save()
        if Team2User.objects.filter(team=team, user=creator).exists():
            creator_nick_name = Team2User.objects.get(team=team, user=creator).nickname
        else:
            creator_nick_name = creator.username
        if creator.avatar.name is None or creator.avatar.name == '':
            creator_avatar = None
        else:
            creator_avatar = settings.BACKEND_URL+creator.avatar.url
        data = {
            'team_id': team_id,
            'project_id': new_project.id,
            'creator_id': creator.id,
            'creator_username': creator.username,
            'creator_nick_name': creator_nick_name,
            'creator_avatar': creator_avatar,
            'introduction': introduction,
            'root_dictionary_id': new_dictionary.id
        }
        return JsonResponse({'errno': 0, 'errmsg': '创建项目成功', 'data': data})

def delete_project(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个项目'})
    if project.status == 1:
        # 项目进入回收站
        if Project2User.objects.filter(project=project, user=user).exists():
            # 判断用户是否是从收藏区删除的
            star_project = Project2User.objects.get(project=project, user=user)
            star_project.delete()
        project.status = -1
        project.save()
        return JsonResponse({'errno': 0, 'errmsg': '已将项目移至回收站'})
    elif project.status == -1:
        # 彻底删除
        project.delete()
        return JsonResponse({'errno': 0, 'errmsg': '删除成功'})

def recover_project(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if not user:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个项目'})
    if project.status == 1:
        return JsonResponse({'errno': 1004, 'errmsg': '您的项目不在回收站中,无需恢复'})
    elif project.status == -1:
        project.status = 1
        project.save()
        return JsonResponse({'errno': 0, 'errmsg': '您的项目已经恢复成功'})
    else:
        return JsonResponse({'errno': 1005, 'errmsg': '没有这个状态的项目'})


def edit_project_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    project_id = body.get('project_id')
    rename = body.get('rename')
    reintroduction = body.get('reintroduction')
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个团队'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '不存在这个项目'})
    if project.status == -1:
        return JsonResponse({'errno': 1005, 'errmsg': '不能对回收站内的项目进行编辑！'})
    if (rename is None or rename == "") and (reintroduction is None or reintroduction == ''):
        return JsonResponse({'errno': 1006, 'errmsg': '不合法的名称及简介'})
    if not (rename is None or rename == ''):
        if Project.objects.filter(name=rename, team=team).exists():
            return JsonResponse({'errno': 1007, 'errmsg': '本团队中已经存在这个名字的项目了'})
        if rename == project.name:
            return JsonResponse({'errno': 1008, 'errmsg': '您新传入的名称一致'})
        project.editor = user
        project.name = rename
        project.save()
    if not (reintroduction is None or reintroduction == ''):
        project.introduction = reintroduction
        project.editor = user
        project.save()
    return JsonResponse({'errno': 0, 'errmsg': '编辑项目成功'})

def star_project(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    project_id = body.get('project_id')
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    if not Team2User.objects.filter(team=team, user=user).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '您还不在这个团队里'})
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1006, 'errmsg': '请传入项目id'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1007, 'errmsg': '没有要收藏的项目'})
    if project.status == -1:
        return JsonResponse({'errno': 1008, 'errmsg': '项目位于回收站中,无法收藏'})
    if Project2User.objects.filter(project=project, user=user, team=team).exists():
        return JsonResponse({'errno': 1009, 'errmsg': '项目已经在“我的收藏”中了,请不要重复收藏'})
    new_star_project = Project2User(project=project, user=user, team=team)
    new_star_project.save()
    return JsonResponse({'errno': 0, 'errmsg': '收藏成功'})

def un_star_project(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    project_id = body.get('project_id')
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    if not Team2User.objects.filter(team=team, user=user).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '您还不在这个团队里'})
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1006, 'errmsg': '请传入项目id'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1007, 'errmsg': '没有要取消收藏的项目'})
    if not Project2User.objects.filter(project=project, user=user, team=team).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '收藏站中不存在此项目'})
    un_star_project = Project2User.objects.get(project=project, user=user, team=team)
    un_star_project.delete()
    return JsonResponse({'errno': 0, 'errmsg': '取消收藏成功'})



# 展示用户收藏的当前团队的所有项目
def show_star_projects(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if not user:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    if not Team2User.objects.filter(team=team, user=user).exists():
        return JsonResponse({'errno': 1005, 'errmsg': '您还不在这个团队里'})
    return_list = []
    if not Project2User.objects.filter(user=user, team=team).exists():
        return JsonResponse({'errno': 1006, 'errmsg': '您还没有收藏任何项目', 'data': return_list})
    star_project = Project2User.objects.filter(user=user, team=team)
    for data in star_project:
        project_value = data.project
        id = project_value.id
        name = project_value.name
        introduction = project_value.introduction
        creator = project_value.creator
        create_time = project_value.create_time
        edit_time = project_value.edit_time
        editor = project_value.editor
        if Team2User.objects.filter(team=team, user=creator).exists():
            creator_nick_name = Team2User.objects.get(team=team, user=creator).nickname
        else:
            creator_nick_name = creator.username
        if Team2User.objects.filter(team=team, user=editor).exists():
            editor_nick_name = Team2User.objects.get(team=team, user=editor).nickname
        else:
            editor_nick_name = editor.username
        if creator.avatar.name is None or creator.avatar.name == '':
            creator_avatar = None
        else:
            creator_avatar = settings.BACKEND_URL+creator.avatar.url
        if editor.avatar.name is None or editor.avatar.name == '':
            editor_avatar = None
        else:
            editor_avatar = settings.BACKEND_URL+editor.avatar.url
        project_info = {
            "project_id": id,
            "name": name,
            "introduction": introduction,
            "creator_id": creator.id,
            "creator_name": creator_nick_name,
            "creator_username": creator.username,
            "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "creator_avatar": creator_avatar,
            "editor_id": editor.id,
            "editor_name": editor_nick_name,
            "editor_username": editor.username,
            "editor_time": edit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "editor_avatar": editor_avatar,
            "tag": 0,
            "star": 1,
        }
        return_list.append(project_info)
    return JsonResponse(({'errno': 0, 'errmsg': '显示收藏区项目成功', 'data': return_list}))


def show_create_projects(request):
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
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    return_list = []
    if not Project.objects.filter(creator=user, team=team).exists():
        return JsonResponse({'errno': 0, 'errmsg': '您还没有在这个团队里创建项目', 'data': return_list})
    project_list = Project.objects.filter(creator=user, team=team)
    for data in project_list:
        if data.status == -1:
            continue
        elif data.status == 1:
            if Project2User.objects.filter(project=data, user=user, team=team).exists():
                # 说明这个项目在本用户收藏的项目中
                star = 1
            else:
                star = 0
            id = data.id
            name = data.name
            introduction = data.introduction
            creator = data.creator
            create_time = data.create_time
            edit_time = data.edit_time
            editor = data.editor
            if Team2User.objects.filter(team=team, user=creator).exists():
                creator_nick_name = Team2User.objects.get(team=team, user=creator).nickname
            else:
                creator_nick_name = creator.username
            if Team2User.objects.filter(team=team, user=editor).exists():
                editor_nick_name = Team2User.objects.get(team=team, user=editor).nickname
            else:
                editor_nick_name = editor.username
            if creator.avatar.name is None or creator.avatar.name == '':
                creator_avatar = None
            else:
                creator_avatar = settings.BACKEND_URL+creator.avatar.url
            if editor.avatar.name is None or editor.avatar.name == '':
                editor_avatar = None
            else:
                editor_avatar = settings.BACKEND_URL+editor.avatar.url
            project_info = {
                "project_id": id,
                "name": name,
                "introduction": introduction,
                'creator_id': creator.id,
                "creator_name": creator_nick_name,
                "creator_username": creator.username,
                'creator_avatar': creator_avatar,
                "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "editor_id": editor.id,
                "editor_name": editor_nick_name,
                "editor_username": editor.username,
                "editor_time": edit_time.strftime("%Y-%m-%d %H:%M:%S"),
                "editor_avatar": editor_avatar,
                "tag": 0,
                "star": star
            }
            return_list.append(project_info)
    return JsonResponse({'errno': 0, 'errmsg': '显示项目信息成功', 'data': return_list})

def team_project_view(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    # 区别要显示的是工作区还是回收站的项目
    status = body.get('status')
    if status != 1 and status != -1:
        return JsonResponse({'errno': 1003, 'errmsg': '没有这种状态'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '不存在这个团队'})
    team2project = Project.objects.filter(team=team, status=status)

    return_list = []
    for data in team2project:
        if Project2User.objects.filter(project=data, user=user, team=team).exists():
            # 说明这个项目在本用户收藏的项目中
            star = 1
        else:
            star = 0
        id = data.id
        name = data.name
        introduction = data.introduction
        creator = data.creator
        create_time = data.create_time
        edit_time = data.edit_time
        editor = data.editor
        if Team2User.objects.filter(team=team, user=creator).exists():
            creator_nick_name = Team2User.objects.get(team=team, user=creator).nickname
        else:
            creator_nick_name = creator.username
        if Team2User.objects.filter(team=team, user=editor).exists():
            editor_nick_name = Team2User.objects.get(team=team, user=editor).nickname
        else:
            editor_nick_name = editor.username
        if creator.avatar.name is None or creator.avatar.name == '':
            creator_avatar = None
        else:
            creator_avatar = settings.BACKEND_URL+creator.avatar.url
        if editor.avatar.name is None or editor.avatar.name == '':
            editor_avatar = None
        else:
            editor_avatar = settings.BACKEND_URL+editor.avatar.url
        project_info = {
            "project_id": id,
            "name": name,
            "introduction": introduction,
            "creator_id": creator.id,
            "creator_name": creator_nick_name,
            "creator_username": creator.username,
            "creator_avatar": creator_avatar,
            "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "editor_id": editor.id,
            "editor_name": editor_nick_name,
            "editor_username": editor.username,
            "editor_avatar": editor_avatar,
            "editor_time": edit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "tag": 0,
            "star": star
        }
        return_list.append(project_info)
    return JsonResponse({'errno': 0, 'errmsg': '显示项目信息成功', 'data':return_list})


def show_single_project_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请您输入正确的项目id'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个项目'})
    if Team2User.objects.filter(team=project.team, user=project.creator).exists():
        creator_nick_name = Team2User.objects.get(team=project.team, user=project.creator).nickname
    else:
        creator_nick_name = project.creator.username
    if Team2User.objects.filter(team=project.team, user=project.editor).exists():
        editor_nick_name = Team2User.objects.get(team=project.team, user=project.editor).nickname
    else:
        editor_nick_name = project.editor.username
    if project.creator.avatar.name is None or project.creator.avatar.name == '':
        creator_avatar = None
    else:
        creator_avatar = settings.BACKEND_URL+project.creator.avatar.url
    if project.editor.avatar.name is None or project.editor.avatar.name == '':
        editor_avatar = None
    else:
        editor_avatar = settings.BACKEND_URL+project.editor.avatar.url
    data = {
        "name": project.name,
        "introduction": project.introduction,
        "creator_username": project.creator.username,
        "creator_email": project.creator.email,
        "creator_name": project.creator.name,
        "creator_id": project.creator.id,
        "creator_nick_name": creator_nick_name,
        "creator_avatar": creator_avatar,
        "create_time": project.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "editor_username": project.editor.username,
        "editor_email": project.editor.email,
        "editor_name": project.editor.name,
        "editor_id": project.editor.id,
        "editor_nick_name": editor_nick_name,
        "editor_avatar": editor_avatar,
        "edit_time": project.edit_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return JsonResponse({'errno': 0, 'errmsg': '查询单个项目信息成功', 'data': data})


def search_sort_project(request):
    global sorted_project_list
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    keyword = body.get('keyword')
    method = body.get('method') #传入创建时间或编辑时间 1为创建时间 2为编辑时间
    order = body.get('order') # order为1则为升序 为2则为降序
    status = body.get('status') # status 为1显示所有项目 为2显示我收藏的项目 为3显示我删除的项目 为4显示我创建的项目
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入正确的团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    if keyword is not None and keyword != "":
        project_keyword_list = Project.objects.filter(name__contains=keyword,team=team)
    else:
        project_keyword_list = Project.objects.filter(team=team)
    if status is None or status not in (1, 2, 3, 4):
        return JsonResponse({'errno': 1005, 'errmsg': '请您传入一个正确的状态'})
    if status == 1:
        # 将所有项目进行排序
        project_list = project_keyword_list.filter(status=1)
    elif status == 2:
        # 创建
        project_list = project_keyword_list.filter(creator=user, status=1)
    elif status == 3:
        # 将我收藏的项目进行排序
        project2user = Project2User.objects.filter(user=user, team=team, project__in=project_keyword_list)
        p_list = project2user.values_list('project', flat=True)
        project_list = Project.objects.filter(id__in=p_list)
        # for project2u in project2user:
        #     if project2u.project in project_keyword_list:
        #         project_list.append(project2u.project)
    elif status == 4:
        # 删除
        project_list = project_keyword_list.filter(status=-1)
    else:
        return JsonResponse({'errno': 1006, 'errmsg': '不存在这种状态的项目'})
    if (method is None or method == '') and (order is None or order == ''):
        # 说明用户只需要搜索，不需要排序
        sorted_project_list = project_list
    else:
        # 说明用户需要进行排序
        if method is None or method not in (1, 2):
            return JsonResponse({'errno': 1007, 'errmsg': '请您传入想要排序的参数'})
        if order is None or order not in (1, 2):
            return JsonResponse({'errno': 1008, 'errmsg': '请您传入想要排序的顺序'})
        if method == 1:
            # 按创建时间排序
            if order == 1:
                sorted_project_list = project_list.order_by('create_time')
            elif order == 2:
                sorted_project_list = project_list.order_by('-create_time')
        elif method == 2:
            # 按编辑时间排序
            if order == 1:
                sorted_project_list = project_list.order_by('edit_time')
            elif order == 2:
                sorted_project_list = project_list.order_by('-edit_time')
    return_list = []
    for data in sorted_project_list:
        if Project2User.objects.filter(project=data, user=user).exists():
            star = 1
        else:
            star = 0
        project_info = {
            "project_id": data.id,
            "name": data.name,
            "introduction": data.introduction,
            "creator_name": data.creator.name,
            "creator_username": data.creator.username,
            "create_time": data.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "editor_name": data.editor.name,
            "editor_username": data.editor.username,
            "editor_time": data.edit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "tag": 0,
            "star": star
        }
        return_list.append(project_info)
    return JsonResponse({'errno': 0, 'errmsg': '排序成功', 'data': return_list})

def copy_project(request):
    # 生成项目副本时不默认收藏，没有简介
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    project_id = body.get('project_id')
    name = body.get('name')
    introduction = body.get('introduction')
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请输入合法的团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有找到这个团队'})
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1005, 'errmsg': '请输入合法的项目id'})
    try:
        project = Project.objects.get(id=project_id, team=team)
    except Exception as e:
        return JsonResponse({'errno': 1006, 'errmsg': '没有找到这个项目'})
    if name is None or name == '':
        return JsonResponse({'errno': 1007, 'errmsg': '请传入合法的项目名'})
    if len(name) > 20:
        return JsonResponse({'errno': 1008, 'errmsg': '您传入的项目名称过长'})
    if introduction is not None and introduction != '':
        if len(introduction) > 100:
            return JsonResponse({'errno': 1009, 'errmsg': '您传入的简介过长'})

    if Project.objects.filter(name=name, team=team).exists():
        return JsonResponse({'errno': 1010, 'errmsg':'您的团队中已有重名的项目'})
    # 创建新项目
    new_project = Project(name=name, introduction=introduction, creator=user, team=team, editor=user)
    new_project.save()
    if Prototype_pages.objects.filter(project=project).exists():
        prototype_page_list = Prototype_pages.objects.filter(project=project).order_by('edit_time')
        for prototype_page in prototype_page_list:
            new_prototype_page = Prototype_pages(name=prototype_page.name, project=new_project, creator=user, editor=prototype_page.editor, content=prototype_page.content)
            new_prototype_page.save()
    # 要复制的项目即使没有根目录也要先创建根文件夹
    new_root = Dictionary(name=new_project.name, project=new_project)
    new_root.save()
    if not Dictionary.objects.filter(name=project.name, project=project, parent_dict=None).exists():
        return JsonResponse({'errno': 1010, 'errmsg': '您要复制的原项目不存在根目录'})
    else:
        root = Dictionary.objects.get(name=project.name, project=project, parent_dict=None)
    copy_sub_dictionary(root, project, new_root, user)

    return JsonResponse({'errno': 0, 'errmsg': '复制项目成功', 'new_project_id': new_project.id})


def copy_sub_dictionary(dictionary, project, new_dictionary, user):
    sub_dictionary_list = Dictionary.objects.filter(parent_dict=dictionary)
    if sub_dictionary_list:
        # 目录下有子目录
        for sub_dictionary in sub_dictionary_list:
            new_sub_dictionary = Dictionary(name=sub_dictionary.name, project=project, parent_dict=new_dictionary)
            new_sub_dictionary.save()
            # documents_list = Documents.objects.filter(doc_dict=sub_dictionary)
            # if documents_list:
            #     # 目录下有文档
            #     for document in documents_list:
            #         new_document = Documents(name=document.name, introduction=document.introduction,
            #                                  project=project,
            #                                  creator=user, editor=document.editor, doc_dict=new_sub_dictionary)
            #         new_document.save()
            #         if Document_history.objects.filter(document=document).exists():
            #             document_history_list = Document_history.objects.filter(document=document).order_by('edit_time')
            #             for document_history in document_history_list:
            #                 new_document_history = Document_history(document=new_document,
            #                                                         editor=document_history.editor,
            #                                                         content=document_history.content)
            #                 new_document_history.save()
            # 递归
            copy_sub_dictionary(sub_dictionary, project, new_sub_dictionary, user)
    # 目录下没有子目录
    documents_list = Documents.objects.filter(doc_dict=dictionary)
    if documents_list:
        # 根目录下有文档
        for document in documents_list:
            new_document = Documents(name=document.name, introduction=document.introduction, project=project,
                                     creator=user, editor=document.editor, doc_dict=new_dictionary)
            new_document.save()
            if Document_history.objects.filter(document=document).exists():
                document_history_list = Document_history.objects.filter(document=document).order_by('edit_time')
                for document_history in document_history_list:
                    new_document_history = Document_history(document=new_document,
                                                            editor=document_history.editor,
                                                            content=document_history.content)
                    new_document_history.save()

