from django.db import migrations


def drop_coach_email(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    column_names = []
    if connection.vendor == "sqlite":
        cursor.execute("PRAGMA table_info(core_coach)")
        column_names = [row[1] for row in cursor.fetchall()]
    elif connection.vendor == "postgresql":
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'core_coach'
            """
        )
        column_names = [row[0] for row in cursor.fetchall()]
    else:
        cursor.execute("SHOW COLUMNS FROM core_coach")
        column_names = [row[0] for row in cursor.fetchall()]

    if "email" in column_names:
        cursor.execute("ALTER TABLE core_coach DROP COLUMN email")


def add_coach_email(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    if connection.vendor == "sqlite":
        cursor.execute("ALTER TABLE core_coach ADD COLUMN email varchar(254) DEFAULT '' NOT NULL")
    else:
        cursor.execute("ALTER TABLE core_coach ADD COLUMN email varchar(254) NOT NULL DEFAULT ''")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_alter_coach_phone"),
    ]

    operations = [
        migrations.RunPython(drop_coach_email, add_coach_email),
    ]
