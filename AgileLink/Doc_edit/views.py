import json
import pdfkit
from markdown import markdown
from django.http import JsonResponse
from django.shortcuts import render
import html2text
# Create your views here.
from Agile_models.models import *
from docx import Document as Document0
import pypandoc


def create_doc(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    name = body.get('name')
    if name is None or name == "":
        return JsonResponse({'errno': 1003, 'errmsg': '不合法的名称'})
    else:
        introduction = body.get('introduction')
        project_id = body.get('project_id')
        dictionary_id = body.get('dictionary_id')
        if project_id is None or project_id == '':
            return JsonResponse({'errno': 1005, 'errmsg': '请输入合法的项目id'})
        try:
            project = Project.objects.get(id=project_id)
        except Exception as e:
            return JsonResponse({'errno': 1006, 'errmsg': '不存在这个项目'})
        if dictionary_id is None or dictionary_id == '':
            return JsonResponse({'errno': 1007, 'errmsg': '请输入合法的文件夹id'})
        if dictionary_id == 0:
            try:
                doc_dict = Dictionary.objects.get(name=project.name, project=project, parent_dict=None)
            except Exception as e:
                return JsonResponse({'errno': 1008, 'errmsg': '不存在这个文件夹'})
        else:
            try:
                doc_dict = Dictionary.objects.get(id=dictionary_id)
            except Exception as e:
                return JsonResponse({'errno': 1009, 'errmsg': '不存在这个文件夹'})
        doc = Documents.objects.filter(name=name, project=project, doc_dict=doc_dict)
        if doc:
            return JsonResponse({'errno': 1010, 'errmsg': '这个文件夹中已经存在这个名称的文档了'})
        new_doc = Documents(name=name, introduction=introduction, project=project,
                            creator=user, editor=user, doc_dict=doc_dict)
        new_doc.save()
        # 需要更新项目的最后编辑时间和最后编辑人
        project.editor = user
        project.save()
        content1 = Document_history.objects.get(id = 140).content
        editor1 = User.objects.get(id = 53)
        document_history1 = Document_history(document=new_doc, editor=editor1,
                                             content=content1)
        document_history1.save()
        content1 = Document_history.objects.get(id = 141).content
        editor2 = User.objects.get(id = 54)
        document_history1 = Document_history(document=new_doc, editor=editor2,
                                                content=content1)
        document_history1.save()
        content1 = Document_history.objects.get(id = 142).content
        editor3 = User.objects.get(id = 55)
        document_history1 = Document_history(document=new_doc, editor=editor3,
                                                content=content1)
        document_history1.save()
        if user.avatar.name is None or user.avatar.name == "":
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + user.avatar.url
        if Team2User.objects.filter(user=new_doc.creator,
                                    team=new_doc.project.team):
            nick_name = Team2User.objects.get(user=new_doc.creator,
                                              team=new_doc.project.team).nickname
        else:
            nick_name = new_doc.creator.username
        data = {
            'doc_id': new_doc.id,
            'name': new_doc.name,
            'introduction': new_doc.introduction,
            'creator_id': new_doc.creator.id,
            'creator_name': nick_name,
            'creator_username': new_doc.creator.username,
            'creator_avatar': avatar_url,
            'editor_id': new_doc.editor.id,
            'editor_name': nick_name,
            'editor_username': new_doc.editor.username,
            'editor_avatar': avatar_url,
            'create_time': new_doc.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            'edit_time': new_doc.edit_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return JsonResponse({'errno': 0, 'errmsg': '创建文档成功', 'data': data})


def rename_doc(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    doc_id = body.get('doc_id')
    rename = body.get('rename')
    re_introduction = body.get('reintroduction')
    try:
        doc = Documents.objects.get(id=doc_id)
    except Exception as e:
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个文档'})
    if (rename is None or rename == "") and (re_introduction is None or re_introduction == ""):
        return JsonResponse({'errno': 1004, 'errmsg': '不合法的名称或简介'})
    if rename is not None and rename != "":
        doc.name = rename
    if re_introduction is not None and re_introduction != "":
        doc.introduction = re_introduction
    doc.save()
    return JsonResponse({'errno': 0, 'errmsg': '编辑文档信息成功'})


def delete_doc(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    doc_id = body.get('doc_id')
    if doc_id is None or not Documents.objects.filter(id=doc_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个文档'})
    doc = Documents.objects.get(id=doc_id)
    doc.delete()
    return JsonResponse({'errno': 0, 'errmsg': '删除文档成功'})


def get_doc_list(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    if project_id is None or not Project.objects.filter(id=project_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个项目'})
    project = Project.objects.get(id=project_id)
    doc_list = Documents.objects.filter(project=project)
    return_list = []
    for doc in doc_list:
        if doc.editor.avatar.name is None or doc.editor.avatar.name == "":
            avatar_url = None
        else:
            avatar_url = settings.BACKEND_URL + doc.editor.avatar.url
        if doc.creator.avatar.name is None or doc.creator.avatar.name == "":
            avatar_url2 = None
        else:
            avatar_url2 = settings.BACKEND_URL + doc.editor.avatar.url
        if Team2User.objects.filter(user=doc.creator, team=doc.project.team):
            creator_nick_name = Team2User.objects.get(user=doc.creator,
                                                      team=doc.project.team).nickname
        else:
            creator_nick_name = doc.creator.username
        if Team2User.objects.filter(user=doc.editor, team=doc.project.team):
            editor_nick_name = Team2User.objects.get(user=doc.editor,
                                                     team=doc.project.team).nickname
        else:
            editor_nick_name = doc.editor.username
        return_list.append({'doc_id': doc.id,
                            'name': doc.name,
                            'introduction': doc.introduction,
                            'creator_id': doc.creator.id,
                            'creator_name': creator_nick_name,
                            'creator_username': doc.creator.username,
                            'creator_avatar': avatar_url2,
                            'editor_id': doc.editor.id,
                            'editor_name': editor_nick_name,
                            'editor_username': doc.editor.username,
                            'editor_avatar': avatar_url,
                            'create_time': doc.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'edit_time': doc.edit_time.strftime("%Y-%m-%d %H:%M:%S")
                            })
    return JsonResponse({'errno': 0, 'errmsg': '获取文档列表成功',
                         'data': {'doc_list': return_list}})


def get_readonly_link(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    doc_id = body.get('doc_id')
    if doc_id is None or not Documents.objects.filter(id=doc_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个文档'})
    doc = Documents.objects.get(id=doc_id)
    return JsonResponse({'errno': 0, 'errmsg': '获取只读链接成功',
                         'data': {'readonly_link': doc.generate_readonly_link()}})


def get_edit_link(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    doc_id = body.get('doc_id')
    if doc_id is None or not Documents.objects.filter(id=doc_id).exists():
        return JsonResponse({'errno': 1003, 'errmsg': '不存在这个文档'})
    doc = Documents.objects.get(id=doc_id)
    return JsonResponse({'errno': 0, 'errmsg': '获取编辑链接成功',
                         'data': {'edit_link': doc.generate_edit_link()}})


def export_doc(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    text = body.get('text')
    if text is None or text == "":
        return JsonResponse({'errno': 1002, 'errmsg': '不合法的文本'})
    name = body.get('name')
    if name is None or name == "":
        return JsonResponse({'errno': 1003, 'errmsg': '不合法的名称'})
    doc_id = body.get('doc_id')
    if doc_id is None or not Documents.objects.filter(id=doc_id).exists():
        return JsonResponse({'errno': 1004, 'errmsg': '不存在这个文档'})
    type0 = body.get('type')
    save_path = settings.MEDIA_ROOT + 'export_doc/' + str(doc_id) + '/'
    os.makedirs(save_path, exist_ok=True)
    save_path = save_path + name
    if type0 == 1:
        markdown0 = html2text.html2text(text)
        save_path = save_path + '.md'
        while os.path.exists(save_path):
            save_path = save_path.split('.')[0] + '_1.' + save_path.split('.')[1]
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(markdown0)
        data = {
            'url': settings.BACKEND_URL + '/media' + save_path.split('media')[1]
        }
        return JsonResponse({'errno': 0, 'errmsg': '导出Markdown成功', 'data': data})
    elif type0 == 2:
        save_path = save_path + '.html'
        while os.path.exists(save_path):
            save_path = save_path.split('.')[0] + '_1.' + save_path.split('.')[1]
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(text)
        data = {
            'url': settings.BACKEND_URL + '/media' + save_path.split('media')[1]
        }
        return JsonResponse({'errno': 0, 'errmsg': '导出HTML成功', 'data': data})
    elif type0 == 3:
        save_path = save_path + '.docx'
        while os.path.exists(save_path):
            save_path = save_path.split('.')[0] + '_1.' + save_path.split('.')[1]
        output = pypandoc.convert_text(text, 'docx', format='html', outputfile=save_path)
        doc = Document0(save_path)
        doc.save(save_path)
        data = {
            'url': settings.BACKEND_URL + '/media' + save_path.split('media')[1]
        }
        return JsonResponse({'errno': 0, 'errmsg': '导出DOCX成功', 'data': data})
    elif type0 == 4:
        save_path = save_path + '.pdf'
        while os.path.exists(save_path):
            save_path = save_path.split('.')[0] + '_1.' + save_path.split('.')[1]
        options = {
            'encoding': "UTF-8"
        }
        pdfkit.from_string(text, save_path, options=options)
        data = {
            'url': settings.BACKEND_URL + '/media' + save_path.split('media')[1]
        }
        return JsonResponse({'errno': 0, 'errmsg': '导出PDF成功', 'data': data})


def create_dictionary(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    name = body.get('name')
    parent_id = body.get('parent_id')
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入正确的项目id'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个项目'})
    if parent_id is None or parent_id == '':
        return JsonResponse({'errno': 1005, 'errmsg': '请传入合法的父文件夹id'})
    try:
        parent_dictionary = Dictionary.objects.get(id=parent_id, project=project)
    except Exception as e:
        return JsonResponse({'errno': 1006, 'errmsg': '不存在这个父文件夹'})
    if name is None or name == '':
        return JsonResponse({'errno': 1007, 'errmsg': '请输入一个合法的文件夹名'})
    if len(name) > 20:
        return JsonResponse({'errno': 1008, 'errmsg': '您的文件夹名过长'})
    if Dictionary.objects.filter(name=name, project=project, parent_dict=parent_dictionary).exists():
        return JsonResponse({'errno': 1009, 'errmsg': '父文件夹中已经存在这个名字的文件夹了'})
    new_dictionary = Dictionary(name=name, project=project, parent_dict=parent_dictionary)
    new_dictionary.save()
    return JsonResponse({'errno': 0, 'errmsg': '创建新文件夹成功', 'dictionary_id': new_dictionary.id})


def delete_dictionary(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入合法的项目id'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '不存在这个项目'})
    dictionary_id = body.get('dictionary_id')
    if dictionary_id is None or dictionary_id == '':
        return JsonResponse({'errno': 1005, 'errmsg': '请传入合法的文件夹id'})
    try:
        dictionary = Dictionary.objects.get(id=dictionary_id, project=project)
    except Exception as e:
        return JsonResponse({'errno': 1006, 'errmsg': '不存在这个文件夹'})
    dictionary.delete()
    return JsonResponse({'errno': 0, 'errmsg': '删除文件夹成功'})


def move_doc(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    team_id = body.get('team_id')
    if team_id is None or team_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请输入合法的团队id'})
    try:
        team = Team.objects.get(id=team_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有这个团队'})
    project_id = body.get('project_id')
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1005, 'errmsg': '请传入合法的项目id'})
    try:
        project = Project.objects.get(id=project_id, team=team)
    except Exception as e:
        return JsonResponse({'errno': 1006, 'errmsg': '团队中没有这个项目'})
    doc_id = body.get('doc_id')
    dict_id = body.get('dict_id')
    if (doc_id is None or doc_id == '') and (dict_id is None or dict_id == ''):
        return JsonResponse({'errno': 1005, 'errmsg': '请传入合法的文档id或文件夹id'})
    dictionary_id = body.get('dictionary_id')  # 要传入的文件夹的id
    if dictionary_id is None or dictionary_id == '':
        return JsonResponse({'errno': 1007, 'errmsg': '请传入合法的文件夹id'})
    try:
        dictionary = Dictionary.objects.get(id=dictionary_id, project=project)
    except Exception as e:
        return JsonResponse({'errno': 1008, 'errmsg': '项目中没有这个文件夹'})
    # 进行判断
    if (doc_id is not None and doc_id != '') and (dict_id is None or dict_id == ''):
        try:
            doc = Documents.objects.get(id=doc_id, project=project)
        except Exception as e:
            return JsonResponse({'errno': 1006, 'errmsg': '项目中没有这个文档'})
        if Documents.objects.filter(name=doc.name, project=project, doc_dict=dictionary).exists():
            # 说明要传入的文件夹中已经有同名文件了
            return JsonResponse({'errno': 1009, 'errmsg': '要传入的文件夹中已经有这个文件了'})
        else:
            doc.doc_dict = dictionary
            doc.save()
    if (doc_id is None or doc_id == '') and (dict_id is not None and dict_id != ''):
        # 移动文件夹到文件夹下
        try:
            dict = Dictionary.objects.get(id=dict_id, project=project)
        except Exception as e:
            return JsonResponse({'errno': 1010, 'errmsg': '项目中没有这个文件夹'})
        if Dictionary.objects.filter(name=dict.name, project=project, parent_dict=dictionary).exists():
            # 说明要传入的文件夹中已经有同名文件夹了
            return JsonResponse({'errno': 1011, 'errmsg': '要传入的文件夹中已经有这个文件夹了'})
        else:
            dict.parent_dict = dictionary
            dict.save()
    if (doc_id is not None and doc_id != '') and (dict_id is not None and dict_id != ''):
        return JsonResponse({'errno': 1012, 'errmsg': '不能一次性移动文档和文件夹！'})

    return JsonResponse({'errno': 0, 'errmsg': '移动文档成功'})


def rename_dictionary(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    dictionary_id = body.get('dictionary_id')
    if dictionary_id is None or dictionary_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入一个合法的文件夹id'})
    try:
        dictionary = Dictionary.objects.get(id=dictionary_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '不存在这个文件夹'})
    if dictionary.parent_dict is None:
        return JsonResponse({'errno': 1005, 'errmsg': '根文件夹的名称不能修改'})
    rename = body.get('rename')
    if rename is None or rename == '':
        return JsonResponse({'errno': 1006, 'errmsg': '请传入合法的文件夹名'})
    if len(rename) > 20:
        return JsonResponse({'errno': 1007, 'errmsg': '您传入的名称过长，请重新传入'})
    parent_dictionary = dictionary.parent_dict
    if Dictionary.objects.filter(name=rename, parent_dict=parent_dictionary).exists():
        return JsonResponse({'errno': 1008, 'errmsg': '当前文件夹中已有重名文件夹'})
    dictionary.name = rename
    dictionary.save()
    return JsonResponse({'errno': 0, 'errmsg': '修改文件夹名称成功'})


def show_file_tree(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'errmsg': '请求方法错误'})
    body = json.loads(request.body)
    token = body.get('token')
    user = auth_token(token)
    if user is None or user is False:
        return JsonResponse({'errno': 1002, 'errmsg': 'token错误或已过期'})
    project_id = body.get('project_id')
    if project_id is None or project_id == '':
        return JsonResponse({'errno': 1003, 'errmsg': '请传入一个合法的项目id'})
    try:
        project = Project.objects.get(id=project_id)
    except Exception as e:
        return JsonResponse({'errno': 1004, 'errmsg': '没有找到这个项目'})

    if not Dictionary.objects.filter(name=project.name, project=project).exists():
        # 说明根文件夹已经被删除
        return JsonResponse({'errno': 1007, 'errmsg': '本项目根文件夹已被删除'})
    try:
        root_dictionary = Dictionary.objects.get(name=project.name, project=project, parent_dict=None)
    except Exception as e:
        return JsonResponse({'errno': 1008, 'errmsg': '没有找到这个文件夹'})
    return_data = {
        "dictionary_id": root_dictionary.id,
        "dictionary_name": root_dictionary.name,
        'sub_dictionaries': show_sub_dictionary(root_dictionary),
        'documents_info': show_document(root_dictionary)
    }
    return JsonResponse({'errno': 0, 'errmsg': '查看文件树成功', 'data': return_data})


def show_sub_dictionary(dictionary):
    dictionary_list = Dictionary.objects.filter(parent_dict=dictionary)
    sub_dictionary_data = []

    for dictionary in dictionary_list:
        data = {
            "dictionary_id": dictionary.id,
            "dictionary_name": dictionary.name,
            "documents_info": show_document(dictionary),
            "sub_dictionaries": show_sub_dictionary(dictionary)
        }
        sub_dictionary_data.append(data)

    return sub_dictionary_data


def show_document(dictionary):
    documents_list = Documents.objects.filter(doc_dict=dictionary)
    document_data = []

    for document in documents_list:
        data = {
            "document_id": document.id,
            "document_name": document.name
        }
        document_data.append(data)

    return document_data
