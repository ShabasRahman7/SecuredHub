from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes

from accounts.models import Tenant, TenantMember
from accounts.permissions import IsTenantOwner
from repositories.models import Repository, RepositoryAssignment


class RepositoryAssignmentListView(APIView):
    """List all assignments for a repository or all repositories with assignments."""
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="List Repository Assignments",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Repository Assignments"]
    )
    def get(self, request, tenant_id, repo_id=None):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        if repo_id:
            repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
            assignments = RepositoryAssignment.objects.filter(repository=repository)
            assigned_member_ids = [a.member.id for a in assignments]
            
            return Response({
                'repository_id': repo_id,
                'assigned_member_ids': assigned_member_ids,
                'assignments': [
                    {
                        'id': a.id,
                        'member_id': a.member.id,
                        'member_email': a.member.user.email,
                        'member_name': a.member.user.get_full_name() or a.member.user.email,
                        'assigned_at': a.assigned_at,
                        'assigned_by': a.assigned_by.email if a.assigned_by else None
                    }
                    for a in assignments
                ]
            }, status=status.HTTP_200_OK)
        else:
            repositories = tenant.repositories.filter(is_active=True)
            result = []
            for repo in repositories:
                assignments = RepositoryAssignment.objects.filter(repository=repo)
                result.append({
                    'repository_id': repo.id,
                    'repository_name': repo.name,
                    'assigned_count': assignments.count(),
                    'assigned_member_ids': [a.member.id for a in assignments]
                })
            return Response({'repositories': result}, status=status.HTTP_200_OK)


class RepositoryAssignmentCreateView(APIView):
    """Assign a repository to a developer."""
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Assign Repository to Developer",
        request=OpenApiTypes.OBJECT,
        responses={201: OpenApiTypes.OBJECT},
        tags=["Repository Assignments"]
    )
    def post(self, request, tenant_id, repo_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
        member_id = request.data.get('member_id')
        
        if not member_id:
            return Response({
                'error': 'member_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        member = get_object_or_404(TenantMember, id=member_id, tenant=tenant)
        
        if RepositoryAssignment.objects.filter(repository=repository, member=member).exists():
            return Response({
                'error': 'Repository is already assigned to this developer'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        assignment = RepositoryAssignment.objects.create(
            repository=repository,
            member=member,
            assigned_by=request.user
        )
        
        return Response({
            'success': True,
            'message': f'Repository assigned to {member.user.email}',
            'assignment': {
                'id': assignment.id,
                'member_id': member.id,
                'member_email': member.user.email,
                'assigned_at': assignment.assigned_at
            }
        }, status=status.HTTP_201_CREATED)


class RepositoryAssignmentDeleteView(APIView):
    """Unassign a repository from a developer."""
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Unassign Repository from Developer",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Repository Assignments"]
    )
    def delete(self, request, tenant_id, repo_id, assignment_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        repository = get_object_or_404(Repository, id=repo_id, tenant=tenant)
        assignment = get_object_or_404(RepositoryAssignment, id=assignment_id, repository=repository)
        
        member_email = assignment.member.user.email
        assignment.delete()
        
        return Response({
            'success': True,
            'message': f'Repository unassigned from {member_email}'
        }, status=status.HTTP_200_OK)


list_repository_assignments = RepositoryAssignmentListView.as_view()
assign_repository = RepositoryAssignmentCreateView.as_view()
unassign_repository = RepositoryAssignmentDeleteView.as_view()

