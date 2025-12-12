# Generated migration for repository assignment tracking

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('repositories', '0006_add_validation_and_metadata_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='RepositoryAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('unassigned_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('assigned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assignments_made', to=settings.AUTH_USER_MODEL)),
                ('developer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repository_assignments', to=settings.AUTH_USER_MODEL)),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='repositories.repository')),
                ('unassigned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assignments_removed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'repository_assignments',
                'ordering': ['-assigned_at'],
                'indexes': [
                    models.Index(fields=['developer', 'is_active'], name='repositories_repositoryassignment_dev_active_idx'),
                    models.Index(fields=['assigned_at'], name='repositories_repositoryassignment_assigned_at_idx'),
                    models.Index(fields=['repository', 'is_active'], name='repositories_repositoryassignment_repo_active_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='repositoryassignment',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('repository', 'developer'), name='unique_active_assignment'),
        ),
    ]