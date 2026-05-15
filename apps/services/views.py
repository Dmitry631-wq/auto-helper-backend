from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Category, Service
from .serializers import CategorySerializer, ServiceSerializer
import requests


class CategoryListView(generics.ListAPIView):
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ServiceListView(generics.ListAPIView):
    serializer_class   = ServiceSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [DjangoFilterBackend, SearchFilter]
    filterset_fields   = ['category__slug']
    search_fields      = ['title', 'description']

    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related('category')


class ServiceDetailView(generics.RetrieveAPIView):
    queryset           = Service.objects.filter(is_active=True)
    serializer_class   = ServiceSerializer
    permission_classes = [permissions.AllowAny]


# ── 2ГИС прокси — запросы идут с сервера, минуя ограничения хоста ──
class TwoGisSearchView(APIView):
    permission_classes = [permissions.AllowAny]
    API_KEY = 'ca10c028-2db8-47ed-9265-315ba35e11d3'

    def get(self, request):
        query = request.query_params.get('q', '')
        try:
            resp = requests.get(
                'https://catalog.api.2gis.com/3.0/items',
                params={
                    'q': f'{query} Абакан',
                    'point': '91.4429,53.7212',
                    'radius': 5000,
                    'fields': 'items.rating,items.stat,items.contact_groups,items.schedule',
                    'key': self.API_KEY,
                },
                timeout=10
            )
            return Response(resp.json())
        except Exception as e:
            return Response({'error': str(e)}, status=503)


class TwoGisReviewsView(APIView):
    permission_classes = [permissions.AllowAny]
    API_KEY = 'ca10c028-2db8-47ed-9265-315ba35e11d3'

    def get(self, request):
        org_id = request.query_params.get('id', '')
        # Пробуем разные endpoint-ы 2ГИС для отзывов
        endpoints = [
            f'https://catalog.api.2gis.com/3.0/reviews',
            f'https://public-api.reviews.2gis.com/2.0/branches/{org_id}/reviews',
        ]
        for url in endpoints:
            try:
                params = {
                    'object_id': org_id,
                    'fields': 'items.user,items.rating,items.text,items.date_created',
                    'sort_by': 'date',
                    'key': self.API_KEY,
                } if 'catalog' in url else {
                    'key': self.API_KEY,
                    'locale': 'ru_RU',
                    'fields': 'meta,reviews',
                }
                resp = requests.get(url, params=params, timeout=10)
                data = resp.json()
                # Если есть отзывы — возвращаем
                if resp.status_code == 200 and (
                        data.get('result', {}).get('items') or
                        data.get('reviews')
                ):
                    return Response(data)
            except Exception:
                continue
        return Response({'result': {'items': []}})