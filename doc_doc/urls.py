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
from doc_doc.core import views_extended
from doc_doc.core import views_downloads
from doc_doc.core import views_bulk
from doc_doc.core import views_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # Main views
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views_dashboard.UserDashboardView.as_view(), name='user_dashboard'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('folder/<int:folder_id>/', views.FolderDetailView.as_view(), name='folder_detail'),

    # Extended views - Favorites, Recent, Trash
    path('favorites/', views_extended.FavoritesView.as_view(), name='favorites'),
    path('recent/', views_extended.RecentFilesView.as_view(), name='recent'),
    path('trash/', views_extended.TrashView.as_view(), name='trash'),
    path('search/', views_extended.SearchView.as_view(), name='search'),

    # File actions
    path('file/<int:file_id>/download/', views_downloads.FileDownloadView.as_view(), name='file_download'),
    path('file/<int:file_id>/preview/', views_downloads.FilePreviewView.as_view(), name='file_preview'),
    path('file/<int:file_id>/serve/', views_downloads.FileServeView.as_view(), name='file_serve'),
    path('file/<int:file_id>/favorite/', views_extended.ToggleFavoriteFileView.as_view(), name='toggle_favorite_file'),
    path('file/<int:file_id>/trash/', views_extended.MoveToTrashFileView.as_view(), name='move_to_trash_file'),
    path('file/<int:file_id>/restore/', views_extended.RestoreFileView.as_view(), name='restore_file'),
    path('file/<int:file_id>/delete/', views_extended.PermanentDeleteFileView.as_view(), name='permanent_delete_file'),

    # Folder actions
    path('folder/<int:folder_id>/favorite/', views_extended.ToggleFavoriteFolderView.as_view(), name='toggle_favorite_folder'),
    path('folder/<int:folder_id>/trash/', views_extended.MoveToTrashFolderView.as_view(), name='move_to_trash_folder'),
    path('folder/<int:folder_id>/restore/', views_extended.RestoreFolderView.as_view(), name='restore_folder'),
    path('folder/<int:folder_id>/delete/', views_extended.PermanentDeleteFolderView.as_view(), name='permanent_delete_folder'),

    # Trash actions
    path('trash/empty/', views_extended.EmptyTrashView.as_view(), name='empty_trash'),

    # Sharing
    path('share/file/<int:file_id>/', views.ShareFileView.as_view(), name='share_file'),
    path('share/folder/<int:folder_id>/', views.ShareFolderView.as_view(), name='share_folder'),
    path('share/<uuid:share_id>/', views.SharedView.as_view(), name='shared_view'),

    # Bulk operations
    path('bulk/files/', views_bulk.BulkFileActionView.as_view(), name='bulk_file_action'),
    path('bulk/folders/', views_bulk.BulkFolderActionView.as_view(), name='bulk_folder_action'),

    # API endpoints
    path('api/storage-usage/', views_extended.StorageUsageView.as_view(), name='storage_usage'),
]

# Error handlers
handler404 = 'doc_doc.core.views.handler404'
handler500 = 'doc_doc.core.views.handler500'
