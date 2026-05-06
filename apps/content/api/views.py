from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from apps.content.api.serializers import ContentItemSerializer
from apps.content.models import ContentItem


class ContentHealthView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "content"})


class ContentItemView(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ContentItemSerializer

    def get_queryset(self):
        user_group_ids = self.request.user.groups.values_list("id", flat=True)
        return ContentItem.objects.filter(allowed_groups__id__in=user_group_ids).distinct().order_by("id")