# Generated manually to add OAuth fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repositories', '0012_add_tenant_credentials'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenantcredential',
            name='github_installation_id',
            field=models.CharField(blank=True, help_text='GitHub App installation ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='tenantcredential',
            name='github_account_login',
            field=models.CharField(blank=True, help_text='GitHub account/organization login', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='tenantcredential',
            name='github_account_id',
            field=models.CharField(blank=True, help_text='GitHub account/organization ID', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='tenantcredential',
            name='granted_scopes',
            field=models.TextField(blank=True, help_text='OAuth scopes granted (comma-separated)', null=True),
        ),
        migrations.AddField(
            model_name='tenantcredential',
            name='oauth_data',
            field=models.JSONField(blank=True, default=dict, help_text='Additional OAuth metadata'),
        ),
        migrations.AlterField(
            model_name='tenantcredential',
            name='encrypted_access_token',
            field=models.TextField(help_text='Encrypted OAuth access token'),
        ),
    ]