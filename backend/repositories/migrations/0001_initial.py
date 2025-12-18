import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('url', models.URLField(max_length=500)),
                ('visibility', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='public', max_length=20)),
                ('default_branch', models.CharField(default='main', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('last_scan_status', models.CharField(blank=True, max_length=50, null=True)),
                ('last_scan_at', models.DateTimeField(blank=True, null=True)),
                ('github_repo_id', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('github_owner', models.CharField(blank=True, max_length=255, null=True)),
                ('github_full_name', models.CharField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_developers', models.ManyToManyField(blank=True, related_name='assigned_repositories', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repositories', to='accounts.tenant')),
            ],
            options={
                'verbose_name': 'Repository',
                'verbose_name_plural': 'Repositories',
                'db_table': 'repositories',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['organization', 'is_active'], name='repositorie_organiz_c1b1ad_idx'), models.Index(fields=['github_repo_id'], name='repositorie_github__05e23b_idx')],
                'unique_together': {('organization', 'url')},
            },
        ),
    ]
