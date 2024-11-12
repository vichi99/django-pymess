from django.db import migrations, models



class Migration(migrations.Migration):
    dependencies = [
        ('pymess', '0030_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name="emailtemplate",
            name="variant",
            field=models.CharField(blank=True, editable=False, max_length=10, null=True),
        ),
        migrations.AlterUniqueTogether(
            name="emailtemplate",
            unique_together={("slug", "locale", "variant")},
        ),
    ]
