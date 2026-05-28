"""
Crea la secuencia PostgreSQL para numeración atómica de tickets.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS tickets_ticket_numero_seq START 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS tickets_ticket_numero_seq;",
        ),
    ]
