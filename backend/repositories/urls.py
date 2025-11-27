"""
URL configuration for repositories app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_repositories, name='list_repositories'),
    path('create/', views.create_repository, name='create_repository'),
    path('<int:repo_id>/', views.get_repository, name='get_repository'),
    path('<int:repo_id>/update/', views.update_repository, name='update_repository'),
    path('<int:repo_id>/delete/', views.delete_repository, name='delete_repository'),
]
