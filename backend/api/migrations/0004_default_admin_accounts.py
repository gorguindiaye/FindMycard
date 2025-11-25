from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_admin_accounts(apps, schema_editor):
    CustomUser = apps.get_model('api', 'CustomUser')
    defaults = [
        {
            'email': 'admin.platform@findmycard.local',
            'first_name': 'Admin',
            'last_name': 'Plateforme',
            'role': 'admin_plateforme',
            'password': 'AdminPlateforme123!',
            'is_superuser': True,
            'is_staff': True,
        },
        {
            'email': 'admin.public@findmycard.local',
            'first_name': 'Admin',
            'last_name': 'Public',
            'role': 'admin_public',
            'password': 'AdminPublic123!',
            'is_superuser': False,
            'is_staff': True,
        },
    ]

    for config in defaults:
        user, created = CustomUser.objects.get_or_create(
            email=config['email'],
            defaults={
                'username': config['email'],
                'first_name': config['first_name'],
                'last_name': config['last_name'],
                'role': config['role'],
                'is_superuser': config['is_superuser'],
                'is_staff': config['is_staff'],
                'is_active': True,
                'password': make_password(config['password']),
            }
        )


def remove_default_admin_accounts(apps, schema_editor):
    CustomUser = apps.get_model('api', 'CustomUser')
    emails = [
        'admin.platform@findmycard.local',
        'admin.public@findmycard.local',
    ]
    CustomUser.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_verificationrequest'),
    ]

    operations = [
        migrations.RunPython(create_default_admin_accounts, remove_default_admin_accounts),
    ]

