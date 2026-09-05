from django.db import migrations

DEFAULT_STATUSES = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]


def seed_statuses(apps, schema_editor):
    OrderStatus = apps.get_model("products_app", "OrderStatus")
    for name in DEFAULT_STATUSES:
        OrderStatus.objects.get_or_create(status=name)


def unseed_statuses(apps, schema_editor):
    # Only remove the defaults we added, and only if no orders reference them.
    OrderStatus = apps.get_model("products_app", "OrderStatus")
    for name in DEFAULT_STATUSES:
        OrderStatus.objects.filter(status=name, order_status__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("products_app", "0031_contactmessage"),
    ]

    operations = [
        migrations.RunPython(seed_statuses, unseed_statuses),
    ]
