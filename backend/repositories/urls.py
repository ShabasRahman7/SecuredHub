"""
URL configuration for repositories app.
"""
from django.urls import path
from .views import repositories, credentials, oauth, assignments

urlpatterns = [
    # Repository endpoints
    path('', repositories.list_repositories, name='list_repositories'),
    path('create/', repositories.create_repository, name='create_repository'),
    
    # Repository assignment endpoints
    path('<int:repo_id>/assignments/', assignments.list_repository_assignments, name='list_repository_assignments'),
    path('<int:repo_id>/assign/', assignments.assign_repository, name='assign_repository'),
    path('<int:repo_id>/assignments/<int:assignment_id>/unassign/', assignments.unassign_repository, name='unassign_repository'),
    
    # Credential endpoints
    path('credentials/', credentials.list_credentials, name='list_credentials'),
    path('credentials/create/', credentials.create_credential, name='create_credential'),
    path('credentials/<int:credential_id>/', credentials.get_credential, name='get_credential'),
    path('credentials/<int:credential_id>/update/', credentials.update_credential, name='update_credential'),
    path('credentials/<int:credential_id>/delete/', credentials.delete_credential, name='delete_credential'),
    
    # OAuth endpoints
    path('credentials/<int:credential_id>/revoke/', oauth.revoke_github_credential, name='revoke_github_credential'),
    path('credentials/<int:credential_id>/repositories/', oauth.github_repositories, name='github_repositories'),
]
