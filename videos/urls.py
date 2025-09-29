from django.urls import path
from . import views

urlpatterns = [
    # Nueva página principal - Landing de ADICLA
    path('', views.landing_page, name='landing'),
    
    # Videos movido aquí
    path('videos/', views.home, name='home'),
    
    # Auth para videos
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Upload (protegido)
    path('upload/', views.upload_media, name='upload'),
    path('edit/<int:media_id>/', views.edit_media, name='edit_media'),
    path('delete/<int:media_id>/', views.delete_media, name='delete_media'),
    
    # Gestión de Tareas
    path('tareas/', views.tareas_dashboard, name='tareas_dashboard'),
    path('tareas/login/', views.tareas_login, name='tareas_login'),
    path('tareas/logout/', views.tareas_logout, name='tareas_logout'),
    
    # Repositorio
    path('repositorio/', views.repositorio_view, name='repositorio'),
    path('repositorio/login/', views.repositorio_login, name='repositorio_login'),
    path('repositorio/logout/', views.repositorio_logout, name='repositorio_logout'),
    path('repositorio/password-reset/', views.repositorio_password_reset, name='repositorio_password_reset'),
    
    # Recuperación de contraseñas
    path('upload/password-reset/', views.upload_password_reset, name='upload_password_reset'),
    path('tareas/password-reset/', views.tareas_password_reset, name='tareas_password_reset'),
    
    # Playlist control
    path('api/playlist/start/', views.start_playlist, name='start_playlist'),
    path('api/playlist/stop/', views.stop_playlist, name='stop_playlist'),
    
    # Sync API
    path('api/sync/', views.sync_status, name='sync_status'),
    path('status/<int:media_id>/', views.media_status, name='media_status'),
]
