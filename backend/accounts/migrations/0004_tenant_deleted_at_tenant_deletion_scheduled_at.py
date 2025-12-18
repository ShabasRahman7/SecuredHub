from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_change_user_tenant_to_onetoone'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='tenant',
            name='deletion_scheduled_at',
            field=models.DateTimeField(blank=True, help_text='Scheduled permanent deletion date', null=True),
        ),
    ]
