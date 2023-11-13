from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pymess', '0028_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailmessage',
            name='pre_header',
            field=models.CharField(blank=True, null=True, max_length=100, verbose_name='pre header'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='pre_header',
            field=models.CharField(blank=True, null=True, max_length=100, verbose_name='pre header'),
        ),
    ]
