from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_auto'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS web_apprating (
                    id bigserial PRIMARY KEY,
                    stars smallint NOT NULL,
                    comment text NOT NULL DEFAULT '',
                    created_at timestamptz NOT NULL DEFAULT now(),
                    user_id bigint NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
                    UNIQUE(user_id)
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS web_apprating;",
            state_operations=[
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
            ],
        ),
    ]
