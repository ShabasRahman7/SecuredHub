# Generated migration for repository validation and metadata fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repositories', '0005_remove_oauth_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='validation_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending Validation'),
                    ('valid', 'Valid'),
                    ('invalid', 'Invalid'),
                    ('access_denied', 'Access Denied'),
                ],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='repository',
            name='validation_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='encrypted_access_token',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='primary_language',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='stars_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='repository',
            name='forks_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='repository',
            name='open_issues_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='repository',
            name='repository_size',
            field=models.IntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name='repository',
            index=models.Index(fields=['validation_status'], name='repositories_validation_status_idx'),
        ),
    ]