from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),           
    path('upload/', views.upload_video, name='upload'), 
    path('edit/<int:video_id>/', views.edit_video, name='edit_video'),
    path('delete/<int:video_id>/', views.delete_video, name='delete_video'),
]
