# Generated manually for comment status field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0002_alter_comment_options_commentgroupobjectpermission_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', '待审核'),
                    ('approved', '已通过'),
                    ('rejected', '已拒绝')
                ],
                default='pending',
                max_length=10,
                verbose_name='审核状态'
            ),
        ),
    ]