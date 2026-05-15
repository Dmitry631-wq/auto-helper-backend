from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='vehicles', verbose_name='Пользователь')
    brand       = models.CharField('Марка', max_length=100)
    model       = models.CharField('Модель', max_length=100)
    year        = models.PositiveSmallIntegerField('Год выпуска')
    mileage     = models.PositiveIntegerField('Текущий пробег (км)')
    drive_style = models.CharField('Стиль езды', max_length=10,
                                   choices=[('city', 'Город'), ('highway', 'Трасса'), ('mixed', 'Смешанный')],
                                   default='mixed')
    last_to_date    = models.DateField('Дата последнего ТО', null=True, blank=True)
    last_to_mileage = models.PositiveIntegerField('Пробег при последнем ТО', null=True, blank=True)
    is_active   = models.BooleanField('Активен', default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.brand} {self.model} ({self.year}) — {self.user}'


class MaintenanceRecord(models.Model):
    """История замен/работ по автомобилю."""
    WORK_TYPES = [
        ('oil',            'Замена масла'),
        ('oil_filter',     'Масляный фильтр'),
        ('air_filter',     'Воздушный фильтр'),
        ('cabin_filter',   'Салонный фильтр'),
        ('fuel_filter',    'Топливный фильтр'),
        ('spark_plugs',    'Свечи зажигания'),
        ('brake_fluid',    'Тормозная жидкость'),
        ('coolant',        'Охлаждающая жидкость'),
        ('transmission',   'Трансмиссионное масло'),
        ('timing_belt',    'Ремень ГРМ'),
        ('brake_pads',     'Тормозные колодки'),
        ('tires',          'Шины'),
        ('battery',        'Аккумулятор'),
        ('other',          'Другое'),
    ]

    vehicle     = models.ForeignKey(Vehicle, on_delete=models.CASCADE,
                                    related_name='records', verbose_name='Автомобиль')
    work_type   = models.CharField('Вид работы', max_length=30, choices=WORK_TYPES)
    date        = models.DateField('Дата замены')
    mileage     = models.PositiveIntegerField('Пробег при замене (км)')
    cost        = models.DecimalField('Стоимость (руб.)', max_digits=10, decimal_places=2,
                                      null=True, blank=True)
    notes       = models.TextField('Примечания', blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Запись ТО'
        verbose_name_plural = 'История ТО'
        ordering            = ['-date']

    def __str__(self):
        return f'{self.get_work_type_display()} — {self.vehicle} ({self.date})'
