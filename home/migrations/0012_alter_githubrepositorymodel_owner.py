# Generated by Django 4.1.12 on 2023-11-10 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_alter_githubrepositorymodel_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='githubrepositorymodel',
            name='owner',
            field=models.JSONField(default=dict),
        ),
    ]
