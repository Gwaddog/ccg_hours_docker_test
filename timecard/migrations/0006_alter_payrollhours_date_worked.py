# Generated by Django 4.2.6 on 2023-11-06 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timecard', '0005_alter_payrollhours_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payrollhours',
            name='date_worked',
            field=models.DateField(),
        ),
    ]
