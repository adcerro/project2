# Generated by Django 5.0 on 2024-01-13 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0004_alter_bid_ammount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=11),
        ),
    ]