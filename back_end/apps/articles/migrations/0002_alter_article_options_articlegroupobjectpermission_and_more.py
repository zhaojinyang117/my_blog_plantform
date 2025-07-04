# Generated by Django 5.2.1 on 2025-06-19 03:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ['-created_at'], 'permissions': [('edit_article', '可以编辑文章'), ('publish_article', '可以发布文章'), ('view_draft_article', '可以查看草稿文章'), ('manage_article', '可以管理文章')], 'verbose_name': '文章', 'verbose_name_plural': '文章'},
        ),
        migrations.CreateModel(
            name='ArticleGroupObjectPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_pk', models.CharField(max_length=255, verbose_name='object ID')),
                ('content_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='articles.article', verbose_name='文章')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group')),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission')),
            ],
            options={
                'verbose_name': '文章组权限',
                'verbose_name_plural': '文章组权限',
            },
        ),
        migrations.CreateModel(
            name='ArticleUserObjectPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_pk', models.CharField(max_length=255, verbose_name='object ID')),
                ('content_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='articles.article', verbose_name='文章')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '文章用户权限',
                'verbose_name_plural': '文章用户权限',
            },
        ),
    ]
