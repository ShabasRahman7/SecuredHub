from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_tenant_deleted_at_tenant_deletion_scheduled_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenantmember',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='tenantmember',
            name='deletion_scheduled_at',
            field=models.DateTimeField(blank=True, help_text='Scheduled permanent deletion date', null=True),
        ),
    ]
