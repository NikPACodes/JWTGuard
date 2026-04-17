from django.db import models
from django.contrib.auth.models import Group


class ContentItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    body = models.TextField()
    allowed_groups = models.ManyToManyField(Group, related_name="content_items", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def is_available_for_user(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False

        user_group_ids = set(user.groups.values_list("id", flat=True))
        allowed_group_ids = set(self.allowed_groups.values_list("id", flat=True))
        return bool(user_group_ids and allowed_group_ids)

    def __str__(self) -> str:
        return self.title