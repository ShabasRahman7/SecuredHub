# Generated migration for chat app
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('scans', '0004_chat_models'),
    ]

    operations = [
        # Since tables already exist, we just create the model definitions
        # without actually creating tables (using Meta db_table to point to existing tables)
    ]
