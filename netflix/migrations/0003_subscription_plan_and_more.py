# Generated by Django 4.0.2 on 2024-12-13 02:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netflix', '0002_alter_subscription_date_subscribed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='plan',
            field=models.CharField(choices=[('Basic', 'Basic'), ('Standard', 'Standard'), ('Premium', 'Premium')], default='Basic', max_length=50),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='subscription_type',
            field=models.CharField(default='HD', max_length=50),
        ),
    ]