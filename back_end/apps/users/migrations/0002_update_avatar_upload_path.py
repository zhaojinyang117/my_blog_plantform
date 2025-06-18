# Generated manually to fix avatar upload path

from django.db import migrations, models
import apps.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, upload_to=apps.users.models.user_avatar_upload_path, verbose_name='头像'),
        ),
    ]
