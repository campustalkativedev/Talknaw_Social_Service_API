# Generated by Django 4.2.6 on 2023-10-13 20:22

import cloudinary_storage.storage
import cloudinary_storage.validators
from django.db import migrations, models
import django.db.models.deletion
import hitcount.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0004_profile_is_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('content', models.TextField()),
                ('voice_recording', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to='recordings/')),
                ('expiry', models.DateTimeField(null=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='users.profile')),
            ],
            options={
                'ordering': ['-date_created'],
            },
            bases=(models.Model, hitcount.models.HitCountMixin),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('clip', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.VideoMediaCloudinaryStorage(), upload_to='videos/', validators=[cloudinary_storage.validators.validate_video])),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='social.post')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pictures', to='social.post')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('content', models.TextField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='social.post')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='users.profile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.UUIDField()),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social.post')),
            ],
        ),
    ]
