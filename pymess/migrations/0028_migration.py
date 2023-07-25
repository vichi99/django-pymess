from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pymess', '0027_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='smstemplate',
            name='is_secret',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='smstemplate',
            name='is_secret',
            field=models.BooleanField(default=True),
        ),
    ]
