from rest_framework import serializers
from apps.content.models import ContentItem


class ContentItemSerializer(serializers.ModelSerializer):
    # Для работы через название групп
    allowed_groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name',
    )

    class Meta:
        model = ContentItem
        fields = ('id', 'title', 'body', 'allowed_groups', 'created_at')


class ContentHealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()