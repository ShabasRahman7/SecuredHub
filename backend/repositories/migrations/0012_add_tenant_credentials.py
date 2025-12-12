# Generated manually to add tenant credentials

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('repositories', '0011_simplify_repository_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Human-readable name for this credential', max_length=255)),
                ('provider', models.CharField(choices=[('github', 'GitHub'), ('gitlab', 'GitLab'), ('bitbucket', 'Bitbucket'), ('azure', 'Azure DevOps')], db_index=True, default='github', max_length=20)),
                ('encrypted_access_token', models.TextField(help_text='Encrypted access token')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_credentials', to='accounts.user')),
                ('tenant', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='credentials', to='accounts.tenant')),
            ],
            options={
                'verbose_name': 'Tenant Credential',
                'verbose_name_plural': 'Tenant Credentials',
                'db_table': 'tenant_credentials',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='repository',
            name='credential',
            field=models.ForeignKey(blank=True, help_text='Credential used for repository access', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repositories', to='repositories.tenantcredential'),
        ),
        migrations.AlterUniqueTogether(
            name='tenantcredential',
            unique_together={('tenant', 'name')},
        ),
    ]