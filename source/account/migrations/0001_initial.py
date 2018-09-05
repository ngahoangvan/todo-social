# Generated by Django 2.0.5 on 2018-09-05 09:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('other_name', models.CharField(blank=True, max_length=255)),
                ('birthday', models.DateField(blank=True, null=True)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('phone_number', models.CharField(blank=True, max_length=255)),
                ('photo_url', models.CharField(blank=True, max_length=255)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(0, 'pending'), (1, 'accepted'), (2, 'declined'), (3, 'blocked')], default=0)),
                ('action_user_id', models.IntegerField()),
                ('user_one', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_one', to=settings.AUTH_USER_MODEL)),
                ('user_two', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_two', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
