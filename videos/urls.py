from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),           
    path('upload/', views.upload_media, name='upload'), 
    path('edit/<int:media_id>/', views.edit_media, name='edit_video'),
    path('delete/<int:media_id>/', views.delete_media, name='delete_media'),
]
