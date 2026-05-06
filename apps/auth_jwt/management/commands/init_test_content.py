from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.content.models import ContentItem


class Command(BaseCommand):
    help = "Создание тест контента."

    def handle(self, *args, **options):
        role_1 = Group.objects.get(name="role_1")
        role_2 = Group.objects.get(name="role_2")

        common_item, _ = ContentItem.objects.get_or_create(
            title="Общий контент",
            defaults={"body": "Виден всем ролям"},
        )
        common_item.allowed_groups.set([role_1, role_2])

        role1_item, _ = ContentItem.objects.get_or_create(
            title="Контент для роли 1",
            defaults={"body": "Виден только роли 1"},
        )
        role1_item.allowed_groups.set([role_1])

        role2_item, _ = ContentItem.objects.get_or_create(
            title="Контент для роли 2",
            defaults={"body": "Виден роли 2"},
        )
        role2_item.allowed_groups.set([role_2])

        self.stdout.write(self.style.SUCCESS("Контент создан успешно."))