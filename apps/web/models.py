from django.db import models


class AppRating(models.Model):
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='app_ratings', verbose_name='Пользователь'
    )
    stars = models.PositiveSmallIntegerField('Оценка')  # 1-5
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Оценка приложения'
        verbose_name_plural = 'Оценки приложения'
        unique_together = ('user',)

    def __str__(self):
        return f'{self.user} — {self.stars}★'
