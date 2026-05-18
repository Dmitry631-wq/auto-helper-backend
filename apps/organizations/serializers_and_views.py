from rest_framework import serializers, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg
from .models import Organization, FavoriteOrganization, Review
from apps.services.serializers import CategorySerializer


class OrganizationSerializer(serializers.ModelSerializer):
    categories       = CategorySerializer(many=True, read_only=True)
    logo             = serializers.SerializerMethodField()
    org_type_display = serializers.SerializerMethodField()
    is_favorite      = serializers.SerializerMethodField()
    services         = serializers.SerializerMethodField()

    class Meta:
        model  = Organization
        fields = [
            'id', 'name', 'address', 'latitude', 'longitude',
            'phone', 'categories', 'logo', 'logo_text', 'logo_color',
            'rating', 'reviews_count', 'work_hours', 'services_list',
            'org_type', 'org_type_display', 'distance_km', 'is_favorite',
            'services',
        ]

    def get_logo(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_org_type_display(self, obj):
        return {
            'service':   'Автосервис',
            'evacuator': 'Эвакуатор',
            'parts':     'Запчасти',
        }.get(obj.org_type, 'Автосервис')

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteOrganization.objects.filter(
                user=request.user, organization=obj).exists()
        return False

    def get_services(self, obj):
        # Сначала берём services_list если заполнен
        if obj.services_list:
            return [s.strip() for s in obj.services_list.split(',') if s.strip()]
        # Иначе берём категории
        cats = [c.name for c in obj.categories.all()]
        if cats:
            return cats
        # Fallback — тип организации
        return [self.get_org_type_display(obj)]


class OrganizationListView(generics.ListAPIView):
    serializer_class   = OrganizationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['categories__slug', 'org_type']
    search_fields      = ['name', 'address']
    ordering_fields    = ['rating', 'name']
    ordering           = ['name']

    def get_queryset(self):
        qs = Organization.objects.filter(is_active=True).prefetch_related('categories')
        org_type = self.request.query_params.get('org_type')
        if org_type:
            qs = qs.filter(org_type=org_type)
        lat_min = self.request.query_params.get('lat_min')
        lat_max = self.request.query_params.get('lat_max')
        lng_min = self.request.query_params.get('lng_min')
        lng_max = self.request.query_params.get('lng_max')
        if all([lat_min, lat_max, lng_min, lng_max]):
            qs = qs.filter(
                latitude__gte=lat_min, latitude__lte=lat_max,
                longitude__gte=lng_min, longitude__lte=lng_max,
            )
        return qs


class OrganizationDetailView(generics.RetrieveAPIView):
    queryset           = Organization.objects.filter(is_active=True)
    serializer_class   = OrganizationSerializer
    permission_classes = [permissions.AllowAny]


class FavoriteListView(generics.ListAPIView):
    serializer_class   = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ids = FavoriteOrganization.objects.filter(
            user=self.request.user).values_list('organization_id', flat=True)
        return Organization.objects.filter(id__in=ids, is_active=True)


class FavoriteToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, org_id):
        try:
            org = Organization.objects.get(id=org_id, is_active=True)
        except Organization.DoesNotExist:
            return Response({'detail': 'Не найдено'}, status=404)
        fav, created = FavoriteOrganization.objects.get_or_create(
            user=request.user, organization=org)
        if not created:
            fav.delete()
            return Response({'is_favorite': False})
        return Response({'is_favorite': True})


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model  = Review
        fields = ['id', 'user_id', 'author_name', 'rating', 'text', 'created_at']
        read_only_fields = ['id', 'user_id', 'author_name', 'created_at']

    def get_author_name(self, obj):
        # Сначала пробуем имя и фамилию из профиля
        first = getattr(obj.user, 'first_name', '') or ''
        last = getattr(obj.user, 'last_name', '') or ''
        full_name = f'{first} {last}'.strip()
        if full_name:
            return full_name
        # Затем поле name
        name = getattr(obj.user, 'name', '') or ''
        if name and name.strip():
            return name.strip()
        # Затем username
        username = getattr(obj.user, 'username', '') or ''
        if username and not username.startswith('reviewer_') and not username.startswith('user_'):
            return username
        # Последний вариант — номер телефона
        phone = getattr(obj.user, 'phone', '') or ''
        if phone and len(phone) >= 4:
            return f'Пользователь {phone[-4:]}'
        return 'Пользователь'

class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Review.objects.filter(
            organization_id=self.kwargs['org_id']).order_by('-created_at')

    def perform_create(self, serializer):
        org = Organization.objects.get(id=self.kwargs['org_id'])
        serializer.save(user=self.request.user, organization=org)
        avg = Review.objects.filter(organization=org).aggregate(
            Avg('rating'))['rating__avg']
        count = Review.objects.filter(organization=org).count()
        org.rating = round(avg, 1)
        org.reviews_count = count
        org.save()
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Review.objects.get(
            id=self.kwargs['review_id'],
            organization_id=self.kwargs['org_id'],
            user=self.request.user
        )
# ═══════════════════════════════════════════════════════════════
# ДОБАВЬ В КОНЕЦ файла apps/organizations/serializers_and_views.py
# ═══════════════════════════════════════════════════════════════

class AppRatingView(APIView):
    """
    GET  /api/organizations/app-rating/ — список всех оценок + средний рейтинг
    POST /api/organizations/app-rating/ — добавить или обновить свою оценку
    """
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.request.method in ('POST', 'DELETE'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request):
        from apps.web.models import AppRating
        from django.db.models import Avg
        ratings = AppRating.objects.select_related('user').order_by('-created_at')
        avg = ratings.aggregate(a=Avg('stars'))['a']
        items = []
        for r in ratings:
            first = getattr(r.user, 'first_name', '') or ''
            last  = getattr(r.user, 'last_name', '') or ''
            name  = (first + ' ' + last).strip()
            if not name:
                phone = getattr(r.user, 'phone', '') or ''
                name = 'Пользователь ' + phone[-4:] if len(phone) >= 4 else 'Пользователь'
            items.append({
                'id':      r.id,
                'uid':     r.user.id,
                'user':    name,
                'stars':   r.stars,
                'comment': r.comment,
                'date':    r.created_at.strftime('%d.%m.%Y'),
            })
        return Response({
            'avg':   round(avg, 1) if avg else None,
            'count': ratings.count(),
            'items': items,
        })

    def post(self, request):
        from apps.web.models import AppRating
        from django.db.models import Avg
        stars   = int(request.data.get('stars', 0))
        comment = request.data.get('comment', '').strip()
        if not 1 <= stars <= 5:
            return Response({'detail': 'Оценка должна быть от 1 до 5'}, status=400)
        AppRating.objects.update_or_create(
            user=request.user,
            defaults={'stars': stars, 'comment': comment}
        )
        avg = AppRating.objects.aggregate(a=Avg('stars'))['a']
        return Response({
            'detail': 'OK',
            'avg':    round(avg, 1) if avg else stars,
            'count':  AppRating.objects.count(),
        })
    def delete(self, request):
    from apps.web.models import AppRating
    try:
        rating = AppRating.objects.get(user=request.user)
        rating.delete()
        return Response({'detail': 'Оценка удалена'})
    except AppRating.DoesNotExist:
        return Response({'detail': 'Оценка не найдена'}, status=404)
