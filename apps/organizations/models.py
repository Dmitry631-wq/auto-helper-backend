from django.db import models
from apps.services.models import Category


class Organization(models.Model):
    name        = models.CharField('Название', max_length=200)
    address     = models.CharField('Адрес', max_length=300)
    latitude    = models.DecimalField('Широта', max_digits=9, decimal_places=6)
    longitude   = models.DecimalField('Долгота', max_digits=9, decimal_places=6)
    phone       = models.CharField('Телефон', max_length=20, blank=True)
    categories  = models.ManyToManyField(Category, blank=True, verbose_name='Категории')
    logo        = models.ImageField('Логотип', upload_to='orgs/', blank=True)

    # Отображение логотипа без картинки
    logo_text   = models.CharField('Текст логотипа', max_length=10, blank=True)
    logo_color  = models.CharField('Цвет логотипа (hex)', max_length=10, default='#C4A882')

    rating      = models.DecimalField('Рейтинг', max_digits=3, decimal_places=1, default=0)
    reviews_count = models.PositiveIntegerField('Количество отзывов', default=0)
    work_hours  = models.CharField('Режим работы', max_length=100, blank=True, default='Пн–Сб: 9:00–19:00')
    services_list = models.CharField('Виды услуг', max_length=500, blank=True, default='')

    # Тип организации для фильтрации
    org_type    = models.CharField(
        'Тип', max_length=20,
        choices=[
            ('service',  'Автосервис'),
            ('evacuator','Эвакуатор'),
            ('parts',    'Запчасти'),
        ],
        default='service',
    )

    distance_km = models.DecimalField('Расстояние (км)', max_digits=5, decimal_places=1,
                                      null=True, blank=True)
    is_active   = models.BooleanField('Активна', default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Организация'
        verbose_name_plural = 'Организации'
        ordering            = ['name']

    def __str__(self):
        return self.name


class FavoriteOrganization(models.Model):
    user         = models.ForeignKey('users.User', on_delete=models.CASCADE,
                                     related_name='favorites', verbose_name='Пользователь')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name='favorited_by', verbose_name='Организация')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Избранная организация'
        verbose_name_plural = 'Избранные организации'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.organization}'


class Review(models.Model):
    user         = models.ForeignKey('users.User', on_delete=models.CASCADE,
                                     related_name='reviews', verbose_name='Пользователь')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name='reviews', verbose_name='Организация')
    rating       = models.PositiveSmallIntegerField('Рейтинг')  # 1-5
    text         = models.TextField('Текст отзыва', blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.user} → {self.organization} ({self.rating}★)'
