import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_accessrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantmember',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_membership', to=settings.AUTH_USER_MODEL),
        ),
    ]
