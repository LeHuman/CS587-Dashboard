# Generated by Django 4.1.12 on 2023-11-10 01:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_alter_githubrepositorymodel_branch_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='githubrepositorymodel',
            name='branch_count',
            field=models.IntegerField(default=1),
        ),
    ]
