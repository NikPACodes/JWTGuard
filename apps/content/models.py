from django.db import models
from django.contrib.auth.models import Group


class ContentItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    body = models.TextField()
    allowed_groups = models.ManyToManyField(Group, related_name="content_items", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Content"
        verbose_name = 'Контент'
        verbose_name_plural = 'Контент'


    def is_available_for_user(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return self.allowed_groups.filter(id__in=user.groups.values_list("id", flat=True)).exists()

    def __str__(self) -> str:
        return self.title