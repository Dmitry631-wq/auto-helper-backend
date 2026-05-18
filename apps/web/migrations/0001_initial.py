from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('stars', models.PositiveSmallIntegerField(verbose_name='Оценка')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='app_ratings',
                    to='users.user',
                    verbose_name='Пользователь'
                )),
            ],
            options={
                'verbose_name': 'Оценка приложения',
                'verbose_name_plural': 'Оценки приложения',
                'unique_together': {('user',)},
            },
        ),
    ]
