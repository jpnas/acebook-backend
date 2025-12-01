from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_clubuser_role_coach"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coach",
            name="phone",
            field=models.CharField(max_length=30),
        ),
    ]
