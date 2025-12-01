from django.db import migrations


LEGACY_COLUMNS = ("email", "specialty", "bio")


def drop_legacy_columns(apps, schema_editor):
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

    for column in LEGACY_COLUMNS:
        if column in column_names:
            cursor.execute(f"ALTER TABLE core_coach DROP COLUMN {column}")


def recreate_legacy_columns(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    for column in LEGACY_COLUMNS:
        if connection.vendor == "sqlite":
            cursor.execute(f"ALTER TABLE core_coach ADD COLUMN {column} varchar(255)")
        else:
            cursor.execute(f"ALTER TABLE core_coach ADD COLUMN {column} varchar(255)")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_remove_coach_email_column"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_columns, recreate_legacy_columns),
    ]
