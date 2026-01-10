from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_aircraft_base_flight_hours_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='aircraft',
            name='show_in_schedule',
            field=models.BooleanField(default=True, verbose_name='Widoczny w harmonogramie'),
        ),
    ]