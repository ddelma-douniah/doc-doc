"""
URL configuration for doc_doc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from doc_doc.core import views
import uuid

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('home/', views.home, name='home'),
    path('folder/<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('share/file/<int:file_id>/', views.share_file, name='share_file'),
    path('share/folder/<int:folder_id>/', views.share_folder, name='share_folder'),
    path('share/<uuid:share_id>/', views.shared_file_view, name='shared_file_view'),
]
