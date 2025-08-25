from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),           
    path('upload/', views.upload_media, name='upload'), 
    path('edit/<int:video_id>/', views.edit_media, name='edit_video'),
    path('delete/<int:video_id>/', views.delete_media, name='delete_video'),
]
