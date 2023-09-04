"""AgileLink URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/team_manage/", include(("Team_manage.urls", "Team_manage"))),
    path("api/v1/public_chat/", include(("Public_chat.urls", "Public_chat"))),
    path("api/v1/notice_center/", include(("Notice_center.urls", "Notice_center"))),
    path("api/v1/project_manage/", include(("Project_manage.urls", "Project_manage"))),
    path("api/v1/prototype_design/", include(("Prototype_design.urls", "Prototype_design"))),
    path("api/v1/doc_edit/", include(("Doc_edit.urls", "Doc_edit"))),
    path("api/v1/agile_models/", include(("Agile_models.urls", "Agile_models"))),
    re_path('^api/v1/media/(?P<path>.*?)$', serve, kwargs={'document_root': settings.MEDIA_ROOT})
]