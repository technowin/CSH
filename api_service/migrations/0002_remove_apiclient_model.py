from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Account", "0011_apiclient"),
        ("api_service", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="APIClient"),
            ],
        ),
    ]
