from rest_framework.response import Response
from rest_framework.views import APIView

#Временная заглушка для создания каркаса
class HealthView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "auth"})