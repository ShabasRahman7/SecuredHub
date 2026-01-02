from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count
from drf_spectacular.utils import extend_schema, OpenApiTypes

from accounts.models import Tenant
from accounts.permissions import IsTenantOwner
from repositories.models import TenantCredential
from repositories.serializers import CredentialSerializer, CredentialCreateSerializer

class CredentialListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="List Credentials",
        responses={200: CredentialSerializer(many=True)},
        tags=["Credentials"]
    )
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        credentials = tenant.credentials.filter(is_active=True).annotate(
            repo_count=Count('repositories', distinct=True)
        ).prefetch_related('repositories')
        
        serializer = CredentialSerializer(credentials, many=True)
        return Response({'credentials': serializer.data}, status=status.HTTP_200_OK)

class CredentialCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Create Credential",
        request=CredentialCreateSerializer,
        responses={201: CredentialSerializer},
        tags=["Credentials"]
    )
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        serializer = CredentialCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        name = serializer.validated_data['name']
        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']

        if TenantCredential.objects.filter(tenant=tenant, name=name).exists():
            return Response({"error": "Credential with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        credential = TenantCredential.objects.create(
            tenant=tenant,
            name=name,
            provider=provider,
            added_by=request.user
        )
        credential.set_access_token(access_token)
        credential.save()
        
        return Response(CredentialSerializer(credential).data, status=status.HTTP_201_CREATED)

class CredentialDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantOwner]

    @extend_schema(
        summary="Get Credential Details",
        responses={200: CredentialSerializer},
        tags=["Credentials"]
    )
    def get(self, request, tenant_id, credential_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant)
        serializer = CredentialSerializer(credential)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Credential",
        request=CredentialCreateSerializer,
        responses={200: CredentialSerializer},
        tags=["Credentials"]
    )
    def put(self, request, tenant_id, credential_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant)
        
        name = request.data.get('name')
        access_token = request.data.get('access_token')
        is_active = request.data.get('is_active')
        
        if name and name != credential.name:
            if TenantCredential.objects.filter(tenant=tenant, name=name).exclude(id=credential.id).exists():
                return Response({"error": "Credential with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
            credential.name = name
        
        if access_token:
            credential.set_access_token(access_token)
        
        if is_active is not None:
            credential.is_active = is_active
        
        credential.save()
        
        return Response(CredentialSerializer(credential).data, status=status.HTTP_200_OK)

    def patch(self, request, tenant_id, credential_id):
        return self.put(request, tenant_id, credential_id)

    @extend_schema(
        summary="Delete Credential",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Credentials"]
    )
    def delete(self, request, tenant_id, credential_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        self.check_object_permissions(request, tenant)
        
        credential = get_object_or_404(TenantCredential, id=credential_id, tenant=tenant)
        
        if credential.repositories.count() > 0:
            return Response({
                "error": f"Cannot delete credential. It is being used by {credential.repositories.count()} repositories."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        credential.delete()
        
        return Response({"message": "Credential deleted successfully"}, status=status.HTTP_200_OK)

list_credentials = CredentialListView.as_view()
create_credential = CredentialCreateView.as_view()
get_credential = CredentialDetailView.as_view()
update_credential = CredentialDetailView.as_view()
delete_credential = CredentialDetailView.as_view()
