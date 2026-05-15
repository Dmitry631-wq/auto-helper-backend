from rest_framework import serializers, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import date, timedelta
from .models import Vehicle, MaintenanceRecord

# ── Нормативы ТО по маркам (км) ──────────────────────────────
# Формат: {марка: {тип_работы: {стиль: интервал}}}
# Если марки нет — используются DEFAULT_INTERVALS

DEFAULT_INTERVALS = {
    'oil':          {'city': 7500,  'highway': 10000, 'mixed': 8000},
    'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 8000},
    'air_filter':   {'city': 15000, 'highway': 20000, 'mixed': 17000},
    'cabin_filter': {'city': 10000, 'highway': 15000, 'mixed': 12000},
    'fuel_filter':  {'city': 30000, 'highway': 40000, 'mixed': 35000},
    'spark_plugs':  {'city': 30000, 'highway': 40000, 'mixed': 35000},
    'brake_fluid':  {'city': 40000, 'highway': 60000, 'mixed': 50000},
    'coolant':      {'city': 60000, 'highway': 80000, 'mixed': 70000},
    'transmission': {'city': 60000, 'highway': 80000, 'mixed': 70000},
    'timing_belt':  {'city': 60000, 'highway': 90000, 'mixed': 75000},
    'brake_pads':   {'city': 30000, 'highway': 50000, 'mixed': 40000},
    'battery':      {'city': 80000, 'highway': 100000,'mixed': 90000},
}

# Нормативы по маркам — отличия от DEFAULT
BRAND_INTERVALS = {
    'Toyota': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 45000, 'highway': 60000, 'mixed': 50000},
        'timing_belt':  {'city': 90000, 'highway': 100000,'mixed': 90000},
        'coolant':      {'city': 80000, 'highway': 100000,'mixed': 90000},
    },
    'Honda': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 40000, 'highway': 50000, 'mixed': 45000},
        'timing_belt':  {'city': 70000, 'highway': 90000, 'mixed': 80000},
    },
    'Volkswagen': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 30000, 'highway': 40000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
        'coolant':      {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'BMW': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
        'coolant':      {'city': 80000, 'highway': 100000,'mixed': 80000},
        'transmission': {'city': 80000, 'highway': 100000,'mixed': 80000},
    },
    'Mercedes-Benz': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
        'coolant':      {'city': 80000, 'highway': 100000,'mixed': 80000},
    },
    'Audi': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
        'timing_belt':  {'city': 60000, 'highway': 90000, 'mixed': 75000},
    },
    'Hyundai': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 40000, 'highway': 50000, 'mixed': 45000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Kia': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 40000, 'highway': 50000, 'mixed': 45000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Nissan': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 40000, 'highway': 50000, 'mixed': 45000},
        'timing_belt':  {'city': 90000, 'highway': 100000,'mixed': 90000},
    },
    'Mazda': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 40000, 'highway': 60000, 'mixed': 50000},
        'timing_belt':  {'city': 80000, 'highway': 100000,'mixed': 90000},
    },
    'Mitsubishi': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 45000, 'mixed': 40000},
        'timing_belt':  {'city': 90000, 'highway': 100000,'mixed': 90000},
    },
    'Subaru': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 40000, 'highway': 50000, 'mixed': 45000},
        'timing_belt':  {'city': 90000, 'highway': 100000,'mixed': 90000},
    },
    'Lada (ВАЗ)': {
        'oil':          {'city': 5000,  'highway': 7500,  'mixed': 5000},
        'oil_filter':   {'city': 5000,  'highway': 7500,  'mixed': 5000},
        'air_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 15000, 'highway': 20000, 'mixed': 15000},
        'timing_belt':  {'city': 60000, 'highway': 75000, 'mixed': 60000},
        'coolant':      {'city': 40000, 'highway': 60000, 'mixed': 45000},
    },
    'Chevrolet': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 40000, 'highway': 60000, 'mixed': 50000},
    },
    'Ford': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 40000, 'highway': 60000, 'mixed': 50000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Renault': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 45000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 75000, 'mixed': 60000},
    },
    'Skoda': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 30000, 'highway': 45000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Peugeot': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 45000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Citroën': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 45000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Lexus': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 50000, 'highway': 60000, 'mixed': 50000},
        'coolant':      {'city': 80000, 'highway': 100000,'mixed': 80000},
    },
    'Volvo': {
        'oil':          {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'oil_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
        'timing_belt':  {'city': 70000, 'highway': 90000, 'mixed': 80000},
    },
    'Opel': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 45000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Geely': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 40000, 'mixed': 30000},
        'timing_belt':  {'city': 60000, 'highway': 80000, 'mixed': 60000},
    },
    'Haval': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 40000, 'mixed': 30000},
    },
    'Chery': {
        'oil':          {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'oil_filter':   {'city': 7500,  'highway': 10000, 'mixed': 7500},
        'spark_plugs':  {'city': 30000, 'highway': 40000, 'mixed': 30000},
    },
    'UAZ': {
        'oil':          {'city': 5000,  'highway': 7500,  'mixed': 5000},
        'oil_filter':   {'city': 5000,  'highway': 7500,  'mixed': 5000},
        'air_filter':   {'city': 10000, 'highway': 15000, 'mixed': 10000},
        'spark_plugs':  {'city': 15000, 'highway': 20000, 'mixed': 15000},
        'timing_belt':  {'city': 50000, 'highway': 60000, 'mixed': 50000},
    },
    'GAZ': {
        'oil':          {'city': 5000,  'highway': 7500,  'mixed': 5000},
        'oil_filter':   {'city': 5000,  'highway': 7500,  'mixed': 5000},
        'spark_plugs':  {'city': 15000, 'highway': 20000, 'mixed': 15000},
    },
    'Tesla': {
        'oil':          {'city': 0,     'highway': 0,     'mixed': 0},      # нет масла
        'oil_filter':   {'city': 0,     'highway': 0,     'mixed': 0},      # нет фильтра
        'spark_plugs':  {'city': 0,     'highway': 0,     'mixed': 0},      # нет свечей
        'brake_fluid':  {'city': 40000, 'highway': 60000, 'mixed': 50000},
        'brake_pads':   {'city': 60000, 'highway': 80000, 'mixed': 70000},  # рекуперация снижает износ
        'cabin_filter': {'city': 15000, 'highway': 20000, 'mixed': 15000},
        'coolant':      {'city': 100000,'highway': 120000,'mixed': 100000},
        'battery':      {'city': 200000,'highway': 250000,'mixed': 200000},
    },
    'BYD': {
        'oil':          {'city': 0,     'highway': 0,     'mixed': 0},
        'oil_filter':   {'city': 0,     'highway': 0,     'mixed': 0},
        'spark_plugs':  {'city': 0,     'highway': 0,     'mixed': 0},
        'brake_fluid':  {'city': 40000, 'highway': 60000, 'mixed': 50000},
        'cabin_filter': {'city': 15000, 'highway': 20000, 'mixed': 15000},
        'coolant':      {'city': 80000, 'highway': 100000,'mixed': 80000},
    },
}

def get_intervals(brand: str) -> dict:
    """Возвращает нормативы для марки, объединяя с DEFAULT."""
    base = {k: dict(v) for k, v in DEFAULT_INTERVALS.items()}
    brand_overrides = BRAND_INTERVALS.get(brand, {})
    for work_type, intervals in brand_overrides.items():
        base[work_type] = intervals
    return base

WORK_NAMES = {
    'oil':          'Замена масла',
    'oil_filter':   'Масляный фильтр',
    'air_filter':   'Воздушный фильтр',
    'cabin_filter': 'Салонный фильтр',
    'fuel_filter':  'Топливный фильтр',
    'spark_plugs':  'Свечи зажигания',
    'brake_fluid':  'Тормозная жидкость',
    'coolant':      'Охлаждающая жидкость',
    'transmission': 'Трансмиссионное масло',
    'timing_belt':  'Ремень ГРМ',
    'brake_pads':   'Тормозные колодки',
    'battery':      'Аккумулятор',
}

COSTS = {
    'oil': 3500, 'oil_filter': 500, 'air_filter': 800,
    'cabin_filter': 600, 'fuel_filter': 1200, 'spark_plugs': 3000,
    'brake_fluid': 1500, 'coolant': 2000, 'transmission': 3500,
    'timing_belt': 8000, 'brake_pads': 5000, 'battery': 6000,
}


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Vehicle
        fields = ['id', 'brand', 'model', 'year', 'mileage', 'drive_style',
                  'last_to_date', 'last_to_mileage', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    work_type_display = serializers.CharField(source='get_work_type_display', read_only=True)

    class Meta:
        model  = MaintenanceRecord
        fields = ['id', 'vehicle', 'work_type', 'work_type_display',
                  'date', 'mileage', 'cost', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class VehicleListCreateView(generics.ListCreateAPIView):
    serializer_class   = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MaintenanceRecordListCreateView(generics.ListCreateAPIView):
    serializer_class   = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vehicle_id = self.kwargs.get('vehicle_id')
        return MaintenanceRecord.objects.filter(
            vehicle__user=self.request.user, vehicle_id=vehicle_id)

    def perform_create(self, serializer):
        vehicle_id = self.kwargs.get('vehicle_id')
        vehicle = Vehicle.objects.get(id=vehicle_id, user=self.request.user)
        record = serializer.save(vehicle=vehicle)
        # Обновляем пробег автомобиля если новый пробег больше текущего
        if record.mileage > vehicle.mileage:
            vehicle.mileage = record.mileage
            vehicle.save()
        # Обновляем данные последнего ТО
        vehicle.last_to_date = record.date
        vehicle.last_to_mileage = record.mileage
        vehicle.save()


class MaintenanceRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MaintenanceRecord.objects.filter(vehicle__user=self.request.user)


class MaintenancePredictView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, vehicle_id):
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, user=request.user)
        except Vehicle.DoesNotExist:
            return Response({'detail': 'Автомобиль не найден.'}, status=404)

        style = vehicle.drive_style
        current_mileage = vehicle.mileage
        intervals = get_intervals(vehicle.brand)

        last_records = {}
        for record in MaintenanceRecord.objects.filter(vehicle=vehicle).order_by('work_type', '-mileage'):
            if record.work_type not in last_records:
                last_records[record.work_type] = record

        predictions = []
        for work_type, name in WORK_NAMES.items():
            interval = intervals[work_type][style]

            # Пропускаем работы с нулевым интервалом (напр. масло у Tesla)
            if interval == 0:
                predictions.append({
                    'work_type': work_type, 'name': name,
                    'last_mileage': None, 'last_date': None,
                    'next_mileage': None, 'km_left': None,
                    'next_date': None, 'status': 'na',
                    'has_data': True, 'estimated_cost': 0,
                })
                continue

            last = last_records.get(work_type)
            if last:
                last_mileage = last.mileage
                last_date = last.date
                has_data = True
            elif vehicle.last_to_mileage:
                last_mileage = vehicle.last_to_mileage
                last_date = vehicle.last_to_date or date.today()
                has_data = True
            else:
                last_mileage = max(0, current_mileage - interval + 1000)
                last_date = date.today()
                has_data = False

            next_mileage = last_mileage + interval
            km_left = next_mileage - current_mileage
            days_left = max(0, km_left // 30)
            next_date = date.today() + timedelta(days=days_left)

            if km_left <= 0:
                status_val = 'overdue'
            elif km_left <= 1000:
                status_val = 'urgent'
            elif km_left <= 3000:
                status_val = 'soon'
            else:
                status_val = 'ok'

            if not has_data:
                status_val = 'unknown'

            predictions.append({
                'work_type': work_type, 'name': name,
                'last_mileage': last_mileage if has_data else None,
                'last_date': last_date.isoformat() if last_date and has_data else None,
                'next_mileage': next_mileage,
                'km_left': km_left,
                'next_date': next_date.isoformat(),
                'status': status_val,
                'has_data': has_data,
                'estimated_cost': COSTS.get(work_type, 0),
                'interval_km': interval,
            })

        order = {'overdue': 0, 'urgent': 1, 'soon': 2, 'ok': 3, 'unknown': 4, 'na': 5}
        predictions.sort(key=lambda x: order.get(x['status'], 5))

        total_cost = sum(p['estimated_cost'] for p in predictions
                        if p['status'] in ('overdue', 'urgent', 'soon'))

        return Response({
            'vehicle': VehicleSerializer(vehicle).data,
            'predictions': predictions,
            'total_upcoming_cost': total_cost,
            'brand_specific': vehicle.brand in BRAND_INTERVALS,
        })


import requests as req
import json as json_lib

class CarBrandsView(APIView):
    permission_classes = [permissions.AllowAny]
    _cache = None

    def get(self, request):
        if CarBrandsView._cache:
            return Response(CarBrandsView._cache)
        try:
            resp = req.get('https://www.carqueryapi.com/api/0.3/?cmd=getMakes',
                           timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            text = resp.text.strip()
            if text.startswith('('): text = text[1:]
            if text.endswith(');'): text = text[:-2]
            data = json_lib.loads(text)
            brands = sorted([m['make_display'] for m in data.get('Makes', [])])
            CarBrandsView._cache = brands
            return Response(brands)
        except Exception as e:
            return Response({'error': str(e)}, status=503)


class CarModelsView(APIView):
    permission_classes = [permissions.AllowAny]
    _cache = {}

    def get(self, request):
        brand = request.query_params.get('brand', '')
        if not brand:
            return Response([])
        if brand in CarModelsView._cache:
            return Response(CarModelsView._cache[brand])
        try:
            resp = req.get(
                f'https://www.carqueryapi.com/api/0.3/?cmd=getModels&make={brand}',
                timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            text = resp.text.strip()
            if text.startswith('('): text = text[1:]
            if text.endswith(');'): text = text[:-2]
            data = json_lib.loads(text)
            models = sorted(list(set([m['model_name'] for m in data.get('Models', [])])))
            CarModelsView._cache[brand] = models
            return Response(models)
        except Exception as e:
            return Response({'error': str(e)}, status=503)


from django.http import HttpResponse

class MaintenancePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, vehicle_id):
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, user=request.user)
        except Vehicle.DoesNotExist:
            return Response({'detail': 'Не найдено'}, status=404)

        records = MaintenanceRecord.objects.filter(vehicle=vehicle).order_by('-date')

        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            import io

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            p.setFont('Helvetica-Bold', 16)
            p.drawString(50, height - 50, f'{vehicle.brand} {vehicle.model} ({vehicle.year})')
            p.setFont('Helvetica', 12)
            p.drawString(50, height - 75, f'Mileage: {vehicle.mileage} km')
            p.line(50, height - 90, width - 50, height - 90)

            y = height - 115
            p.setFont('Helvetica-Bold', 11)
            p.drawString(50, y, 'Date'); p.drawString(150, y, 'Work type')
            p.drawString(370, y, 'Mileage'); p.drawString(450, y, 'Cost')
            y -= 20; p.setFont('Helvetica', 10)

            for record in records:
                if y < 60:
                    p.showPage(); y = height - 50; p.setFont('Helvetica', 10)
                p.drawString(50, y, record.date.strftime('%d.%m.%Y'))
                p.drawString(150, y, record.get_work_type_display()[:28])
                p.drawString(370, y, f'{record.mileage} km')
                p.drawString(450, y, f'{record.cost} rub.' if record.cost else '—')
                y -= 18

            p.save(); buffer.seek(0)
            filename = f'maintenance_{vehicle.brand}_{vehicle.model}.pdf'
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except ImportError:
            import csv
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="maintenance.csv"'
            response.write('\ufeff')
            writer = csv.writer(response)
            writer.writerow(['Дата', 'Вид работы', 'Пробег (км)', 'Стоимость (руб.)', 'Примечания'])
            for record in records:
                writer.writerow([record.date.strftime('%d.%m.%Y'),
                    record.get_work_type_display(), record.mileage,
                    record.cost or '', record.notes])
            return response
