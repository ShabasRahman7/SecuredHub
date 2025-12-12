# Generated manually to simplify repository model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repositories', '0010_migrate_repository_tokens'),
    ]

    operations = [
        # Remove complex fields that we don't need
        migrations.RemoveField(
            model_name='repository',
            name='visibility',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='last_scan_status',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='last_scan_at',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='validation_status',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='validation_message',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='encrypted_access_token',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='github_repo_id',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='github_owner',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='github_full_name',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='primary_language',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='stars_count',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='forks_count',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='open_issues_count',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='repository_size',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='assigned_developers',
        ),
        migrations.RemoveField(
            model_name='repository',
            name='credential',
        ),
        
        # Remove the RepositoryAssignment model entirely
        migrations.DeleteModel(
            name='RepositoryAssignment',
        ),
        
        # Remove the TenantRepositoryCredential model entirely
        migrations.DeleteModel(
            name='TenantRepositoryCredential',
        ),
    ]