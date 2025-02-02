# Generated by Django 4.0.2 on 2024-12-21 15:56

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=150)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('resolution', models.CharField(choices=[('HD', 'HD'), ('FHD', 'Full HD'), ('UHD', 'Ultra HD')], max_length=10)),
                ('watch_count', models.IntegerField(default=0)),
                ('file', models.FileField(upload_to='movies/')),
                ('thumbnail', models.ImageField(upload_to='thumbnail/')),
                ('preview_image', models.ImageField(upload_to='preview_images/')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='netflix.category')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('movies_watched', models.IntegerField(default=0)),
                ('liked_movies', models.ManyToManyField(blank=True, related_name='liked_profiles', to='netflix.Movie')),
                ('preferred_categories', models.ManyToManyField(blank=True, to='netflix.Category')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=150)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='netflix.movie')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlists', to='netflix.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False)),
                ('date_subscribed', models.DateTimeField(blank=True, null=True)),
                ('date_expired', models.DateTimeField(blank=True, null=True)),
                ('plan', models.CharField(choices=[('Basic', 'Basic'), ('Standard', 'Standard'), ('Premium', 'Premium')], default='Basic', max_length=50)),
                ('subscription_type', models.CharField(default='HD', max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to='netflix.subscription'),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=datetime.datetime(2024, 12, 21, 15, 56, 41, 59172, tzinfo=utc))),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='movie',
            name='tags',
            field=models.ManyToManyField(to='netflix.Tag'),
        ),
        migrations.CreateModel(
            name='WatchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('watched_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='netflix.movie')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='netflix.profile')),
            ],
            options={
                'ordering': ['-watched_at'],
                'unique_together': {('profile', 'movie')},
            },
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_liked', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='netflix.movie')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='netflix.profile')),
            ],
            options={
                'unique_together': {('profile', 'movie')},
            },
        ),
    ]
