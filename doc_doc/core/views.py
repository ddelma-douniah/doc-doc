from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Folder, File, Share
import uuid

@login_required
def dashboard(request):
    if request.method == 'POST':
        if 'create_folder' in request.POST:
            folder_name = request.POST.get('folder_name')
            if folder_name:
                Folder.objects.create(name=folder_name, owner=request.user)
                messages.success(request, 'Folder created successfully.')
            else:
                messages.error(request, 'Folder name is required.')
        elif 'upload_file' in request.POST:
            file = request.FILES.get('file')
            if file:
                File.objects.create(name=file.name, file=file, owner=request.user, folder=None)
                messages.success(request, 'File uploaded successfully.')
            else:
                messages.error(request, 'File is required.')
        return redirect('dashboard')

    folders = Folder.objects.filter(owner=request.user, parent__isnull=True)
    files = File.objects.filter(owner=request.user, folder__isnull=True)
    return render(request, 'dashboard.html', {'folders': folders, 'files': files})

@login_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    if request.method == 'POST':
        if 'create_folder' in request.POST:
            folder_name = request.POST.get('folder_name')
            if folder_name:
                Folder.objects.create(name=folder_name, owner=request.user, parent=folder)
                messages.success(request, 'Folder created successfully.')
            else:
                messages.error(request, 'Folder name is required.')
        elif 'upload_file' in request.POST:
            file = request.FILES.get('file')
            if file:
                File.objects.create(name=file.name, file=file, owner=request.user, folder=folder)
                messages.success(request, 'File uploaded successfully.')
            else:
                messages.error(request, 'File is required.')
        return redirect('folder_detail', folder_id=folder.id)

    folders = Folder.objects.filter(owner=request.user, parent=folder)
    files = File.objects.filter(owner=request.user, folder=folder)
    return render(request, 'folder_detail.html', {'folder': folder, 'folders': folders, 'files': files})

@login_required
def share_file(request, file_id):
    file = get_object_or_404(File, id=file_id, owner=request.user)
    share, created = Share.objects.get_or_create(file=file)
    share_url = request.build_absolute_uri(f'/share/{share.id}/')
    return render(request, 'share_link.html', {'share_url': share_url})

@login_required
def share_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
    share, created = Share.objects.get_or_create(folder=folder)
    share_url = request.build_absolute_uri(f'/share/{share.id}/')
    return render(request, 'share_link.html', {'share_url': share_url})

def shared_file_view(request, share_id):
    share = get_object_or_404(Share, id=share_id)
    if share.file:
        return render(request, 'shared_file.html', {'file': share.file})
    else:
        return render(request, 'shared_folder.html', {'folder': share.folder})

def home(request):
    return render(request, 'home.html')
