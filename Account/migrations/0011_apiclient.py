from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Account", "0010_passwordchangelog"),
        ("api_service", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="APIClient",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("client_id", models.CharField(max_length=100, unique=True)),
                        ("client_secret", models.CharField(blank=True, default="", max_length=255)),
                        ("is_active", models.BooleanField(default=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={"db_table": "api_client"},
                ),
            ],
        ),
    ]
