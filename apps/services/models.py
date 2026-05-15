# ── models.py ─────────────────────────────────────────────────
from django.db import models


class Category(models.Model):
    name  = models.CharField('Название', max_length=100)
    slug  = models.SlugField(unique=True)
    icon  = models.CharField('Иконка (emoji/icon-name)', max_length=50, blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order']

    def __str__(self):
        return self.name


class Service(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                    related_name='services', verbose_name='Категория')
    title       = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    image       = models.ImageField('Изображение', upload_to='services/', blank=True)
    is_active   = models.BooleanField('Активна', default=True)
    order       = models.PositiveSmallIntegerField('Порядок', default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title
