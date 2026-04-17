from rest_framework import serializers
from apps.content.models import ContentItem


class ContentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = ("id", "title", "body", "visibility", "created_at")