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
    
    # Gestión de Tareas - Dashboard y Auth
    path('tareas/', views.tareas_dashboard, name='tareas_dashboard'),
    path('tareas/login/', views.tareas_login, name='tareas_login'),
    path('tareas/logout/', views.tareas_logout, name='tareas_logout'),
    
    # Gestión de Proyectos
    path('tareas/proyectos/', views.proyectos_lista, name='proyectos_lista'),
    path('tareas/proyectos/crear/', views.proyecto_crear, name='proyecto_crear'),
    path('tareas/proyectos/<int:pk>/', views.proyecto_detalle, name='proyecto_detalle'),
    path('tareas/proyectos/<int:pk>/editar/', views.proyecto_editar, name='proyecto_editar'),
    path('tareas/proyectos/<int:pk>/eliminar/', views.proyecto_eliminar, name='proyecto_eliminar'),
    
    # Gestión de Tareas
    path('tareas/mis-tareas/', views.tareas_lista, name='tareas_lista'),
    path('tareas/crear/', views.tarea_crear, name='tarea_crear'),
    path('tareas/crear/<int:proyecto_pk>/', views.tarea_crear, name='tarea_crear_proyecto'),
    path('tareas/tarea/<int:tarea_id>/', views.tarea_detalle, name='tarea_detalle'),
    path('tareas/tarea/<int:tarea_id>/editar/', views.tarea_editar, name='tarea_editar'),
    path('tareas/tarea/<int:tarea_id>/eliminar/', views.tarea_eliminar, name='tarea_eliminar'),
    path('tareas/tarea/<int:tarea_id>/estado/', views.tarea_cambiar_estado, name='tarea_cambiar_estado'),
    
    # Comentarios
    path('tareas/proyecto/<int:proyecto_id>/comentario/', views.comentario_proyecto_crear, name='comentario_proyecto_crear'),
    path('tareas/tarea/<int:tarea_id>/comentario/', views.comentario_tarea_crear, name='comentario_tarea_crear'),
    
    # Archivos
    path('tareas/tarea/<int:tarea_id>/archivo/', views.tarea_archivo_crear, name='tarea_archivo_crear'),
    path('tareas/archivo/<str:tipo>/<int:archivo_id>/descargar/', views.archivo_descargar, name='archivo_descargar'),
    path('tareas/archivo/<str:tipo>/<int:archivo_id>/previsualizar/', views.archivo_previsualizar, name='archivo_previsualizar'),
    
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
