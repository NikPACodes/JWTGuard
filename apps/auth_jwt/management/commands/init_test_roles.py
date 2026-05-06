from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Создание тестовых Groups(ролей) и Permissions"

    @transaction.atomic
    def handle(self, *args, **options):
        Group.objects.get_or_create(name="role_1")
        Group.objects.get_or_create(name="role_2")
        self.stdout.write(self.style.SUCCESS("Groups и permissions созданы успешно."))