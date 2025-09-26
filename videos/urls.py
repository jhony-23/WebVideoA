from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Upload (protegido)
    path('upload/', views.upload_media, name='upload'),
    path('edit/<int:media_id>/', views.edit_media, name='edit_media'),
    path('delete/<int:media_id>/', views.delete_media, name='delete_media'),
    
    # Playlist control
    path('api/playlist/start/', views.start_playlist, name='start_playlist'),
    path('api/playlist/stop/', views.stop_playlist, name='stop_playlist'),
    
    # Sync API
    path('api/sync/', views.sync_status, name='sync_status'),
    path('status/<int:media_id>/', views.media_status, name='media_status'),
]
