from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count
from django.utils import timezone

from apps.organizations.models import Organization, Review
from apps.garage.models import Vehicle
from apps.users.models import User
from .models import AppRating


# ── Главная ──────────────────────────────────────────────────
def home(request):
    orgs_count = Organization.objects.filter(is_active=True).count()
    reviews_count = Review.objects.count()
    app_rating = AppRating.objects.aggregate(avg=Avg('stars'))['avg']
    app_rating_count = AppRating.objects.count()
    top_orgs = Organization.objects.filter(is_active=True).order_by('-rating')[:3]
    return render(request, 'web/home.html', {
        'orgs_count': orgs_count,
        'reviews_count': reviews_count,
        'app_rating': round(app_rating, 1) if app_rating else None,
        'app_rating_count': app_rating_count,
        'top_orgs': top_orgs,
    })


# ── Организации ───────────────────────────────────────────────
def catalog(request):
    org_type = request.GET.get('type', '')
    search = request.GET.get('q', '')
    orgs = Organization.objects.filter(is_active=True)
    if org_type in ('service', 'evacuator', 'parts'):
        orgs = orgs.filter(org_type=org_type)
    if search:
        orgs = orgs.filter(name__icontains=search)
    orgs = orgs.order_by('distance_km', 'name')
    return render(request, 'web/catalog.html', {
        'orgs': orgs,
        'org_type': org_type,
        'search': search,
    })


def org_detail(request, pk):
    org = get_object_or_404(Organization, pk=pk, is_active=True)
    reviews = Review.objects.filter(organization=org).select_related('user').order_by('-created_at')
    avg = reviews.aggregate(avg=Avg('rating'))['avg']
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    return render(request, 'web/org_detail.html', {
        'org': org,
        'reviews': reviews,
        'avg': round(avg, 1) if avg else None,
        'user_review': user_review,
        'services': [s.strip() for s in org.services_list.split(',') if s.strip()],
    })


@login_required
@require_POST
def add_review(request, pk):
    org = get_object_or_404(Organization, pk=pk, is_active=True)
    rating = int(request.POST.get('rating', 0))
    text = request.POST.get('text', '').strip()
    if not 1 <= rating <= 5:
        messages.error(request, 'Выберите оценку от 1 до 5')
        return redirect('web:org_detail', pk=pk)
    review, created = Review.objects.update_or_create(
        user=request.user, organization=org,
        defaults={'rating': rating, 'text': text}
    )
    # Обновляем рейтинг организации
    avg = Review.objects.filter(organization=org).aggregate(avg=Avg('rating'))['avg']
    org.rating = round(avg, 1) if avg else 0
    org.reviews_count = Review.objects.filter(organization=org).count()
    org.save()
    messages.success(request, 'Отзыв сохранён!')
    return redirect('web:org_detail', pk=pk)


@login_required
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    org = review.organization
    review.delete()
    avg = Review.objects.filter(organization=org).aggregate(avg=Avg('rating'))['avg']
    org.rating = round(avg, 1) if avg else 0
    org.reviews_count = Review.objects.filter(organization=org).count()
    org.save()
    messages.success(request, 'Отзыв удалён')
    return redirect('web:org_detail', pk=org.pk)


# ── Отзывы ───────────────────────────────────────────────────
def reviews(request):
    org_filter = request.GET.get('org', '')
    all_reviews = Review.objects.select_related('user', 'organization').order_by('-created_at')
    if org_filter:
        all_reviews = all_reviews.filter(organization__name__icontains=org_filter)
    orgs_with_reviews = Organization.objects.filter(
        reviews__isnull=False, is_active=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).distinct().order_by('-avg_rating')
    return render(request, 'web/reviews.html', {
        'orgs_with_reviews': orgs_with_reviews,
        'org_filter': org_filter,
    })


# ── FAQ ──────────────────────────────────────────────────────
def faq(request):
    faqs = [
        {'q': 'Как скачать приложение?',
         'a': 'Нажмите кнопку «Скачать APK» на главной странице. Разрешите установку из неизвестных источников в настройках Android и установите файл.'},
        {'q': 'Приложение бесплатное?',
         'a': 'Да, полностью бесплатно для жителей Абакана. Никаких скрытых платежей нет.'},
        {'q': 'Как добавить автомобиль в гараж?',
         'a': 'Войдите в аккаунт, перейдите в «Гараж» и нажмите «+ Добавить авто». Выберите марку, модель, год и укажите пробег.'},
        {'q': 'Как вызвать эвакуатор?',
         'a': 'На главной странице нажмите «Вызвать эвакуатор». Также можно позвонить из раздела «Организации».'},
        {'q': 'Можно ли добавить свою организацию?',
         'a': 'Напишите нам на mikshindima89@gmail.com — рассмотрим заявку.'},
        {'q': 'Работает ли приложение без интернета?',
         'a': 'Список организаций, контакты и гараж работают офлайн. Для карты нужен интернет.'},
        {'q': 'Как оставить отзыв?',
         'a': 'Перейдите на страницу организации, войдите в аккаунт и нажмите «Написать отзыв».'},
        {'q': 'Как восстановить пароль?',
         'a': 'На странице входа нажмите «Забыли пароль?», введите email — придёт код для сброса пароля.'},
    ]
    return render(request, 'web/faq.html', {'faqs': faqs})


# ── Авторизация ───────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('web:profile')
    if request.method == 'POST':
        login_field = request.POST.get('login', '').strip()
        password = request.POST.get('password', '')
        user = None
        # Попытка войти по email
        if '@' in login_field:
            try:
                u = User.objects.get(email=login_field)
                if u.check_password(password):
                    user = u
            except User.DoesNotExist:
                pass
        else:
            # По телефону
            phone = login_field.replace(' ', '').replace('-', '')
            if phone.startswith('8') and len(phone) == 11:
                phone = '+7' + phone[1:]
            elif phone.startswith('7') and len(phone) == 11:
                phone = '+' + phone
            try:
                u = User.objects.get(phone=phone)
                if u.check_password(password):
                    user = u
            except User.DoesNotExist:
                pass
        if user and user.is_active:
            login(request, user)
            next_url = request.GET.get('next', 'web:profile')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email/телефон или пароль')
    return render(request, 'web/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('web:profile')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not first_name:
            messages.error(request, 'Введите имя')
        elif not (email or phone):
            messages.error(request, 'Укажите email или телефон')
        elif len(password) < 6:
            messages.error(request, 'Пароль минимум 6 символов')
        elif password != password2:
            messages.error(request, 'Пароли не совпадают')
        elif phone and User.objects.filter(phone=phone).exists():
            messages.error(request, 'Пользователь с таким телефоном уже существует')
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
        else:
            # Нормализуем телефон
            if phone:
                phone = phone.replace(' ', '').replace('-', '')
                if phone.startswith('8') and len(phone) == 11:
                    phone = '+7' + phone[1:]
            user = User.objects.create_user(
                phone=phone or email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            login(request, user)
            messages.success(request, f'Добро пожаловать, {first_name}!')
            return redirect('web:profile')
    return render(request, 'web/register.html')


def logout_view(request):
    logout(request)
    return redirect('web:home')


# ── Профиль ───────────────────────────────────────────────────
@login_required
def profile(request):
    user = request.user
    cars = Car.objects.filter(user=user) if hasattr(user, 'cars') else []
    my_reviews = Review.objects.filter(user=user).select_related('organization').order_by('-created_at')
    app_rating = AppRating.objects.filter(user=user).first()
    return render(request, 'web/profile.html', {
        'user': user,
        'cars': cars,
        'my_reviews': my_reviews,
        'app_rating': app_rating,
        'cars_count': len(list(cars)),
        'reviews_count': my_reviews.count(),
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        new_pass = request.POST.get('new_password', '')
        old_pass = request.POST.get('old_password', '')
        if new_pass:
            if not user.check_password(old_pass):
                messages.error(request, 'Неверный текущий пароль')
                return redirect('web:edit_profile')
            if len(new_pass) < 6:
                messages.error(request, 'Пароль минимум 6 символов')
                return redirect('web:edit_profile')
            user.set_password(new_pass)
            login(request, user)
        user.save()
        messages.success(request, 'Профиль обновлён ✓')
        return redirect('web:profile')
    return render(request, 'web/edit_profile.html', {'user': request.user})


# ── Гараж ────────────────────────────────────────────────────
@login_required
def garage(request):
    cars = Car.objects.filter(user=request.user).order_by('-created_at') if hasattr(request.user, 'cars') else []
    return render(request, 'web/garage.html', {'cars': list(cars)})


@login_required
@require_POST
def add_car(request):
    make = request.POST.get('make', '').strip()
    model = request.POST.get('model', '').strip()
    year = request.POST.get('year', '')
    mileage = request.POST.get('mileage', 0)
    engine_type = request.POST.get('engine_type', 'Бензин')
    last_to_date = request.POST.get('last_to_date') or None
    if not make or not model or not year:
        messages.error(request, 'Заполните марку, модель и год')
        return redirect('web:garage')
    Car.objects.create(
        user=request.user,
        make=make, model=model, year=year,
        mileage=mileage, engine_type=engine_type,
        last_to_date=last_to_date,
    )
    messages.success(request, f'{make} {model} добавлен в гараж 🚗')
    return redirect('web:garage')


@login_required
@require_POST
def delete_car(request, pk):
    car = get_object_or_404(Car, pk=pk, user=request.user)
    name = f'{car.make} {car.model}'
    car.delete()
    messages.success(request, f'{name} удалён')
    return redirect('web:garage')


@login_required
def edit_car(request, pk):
    car = get_object_or_404(Car, pk=pk, user=request.user)
    if request.method == 'POST':
        car.make = request.POST.get('make', car.make)
        car.model = request.POST.get('model', car.model)
        car.year = request.POST.get('year', car.year)
        car.mileage = request.POST.get('mileage', car.mileage)
        car.engine_type = request.POST.get('engine_type', car.engine_type)
        car.last_to_date = request.POST.get('last_to_date') or None
        car.save()
        messages.success(request, 'Автомобиль обновлён ✓')
        return redirect('web:garage')
    return render(request, 'web/edit_car.html', {'car': car})


# ── Оценка приложения ────────────────────────────────────────
@login_required
@require_POST
def rate_app(request):
    stars = int(request.POST.get('stars', 0))
    comment = request.POST.get('comment', '').strip()
    if not 1 <= stars <= 5:
        messages.error(request, 'Выберите оценку')
        return redirect('web:home')
    AppRating.objects.update_or_create(
        user=request.user,
        defaults={'stars': stars, 'comment': comment}
    )
    messages.success(request, f'Спасибо за оценку {"★" * stars}')
    return redirect('web:home')


# ── Восстановление пароля ─────────────────────────────────────
def forgot_password(request):
    step = request.session.get('recovery_step', 1)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_email':
            email = request.POST.get('email', '').strip()
            try:
                user = User.objects.get(email=email)
                import random, string
                from apps.users.models import SmsCode
                code = ''.join(random.choices(string.digits, k=4))
                SmsCode.objects.filter(phone=user.phone, purpose='reset').delete()
                SmsCode.objects.create(phone=user.phone, code=code, purpose='reset')
                # Send via Resend
                from django.conf import settings
                import requests as req
                api_key = getattr(settings, 'RESEND_API_KEY', '')
                if api_key:
                    req.post('https://api.resend.com/emails',
                        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                        json={'from': 'Авто-помощник <noreply@auto-helper-abakan.online>',
                              'to': [email],
                              'subject': 'Восстановление пароля — Авто-помощник',
                              'text': f'Ваш код: {code}\n\nКод действителен 10 минут.'},
                        timeout=10)
                request.session['recovery_phone'] = user.phone
                request.session['recovery_step'] = 2
                messages.success(request, f'Код отправлен на {email}')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь с таким email не найден')
        elif action == 'verify_code':
            from apps.users.models import SmsCode
            phone = request.session.get('recovery_phone', '')
            code = request.POST.get('code', '').strip()
            try:
                sms = SmsCode.objects.filter(phone=phone, purpose='reset').latest('created_at')
                if sms.is_expired():
                    messages.error(request, 'Код истёк. Запросите новый.')
                elif sms.code != code:
                    messages.error(request, 'Неверный код')
                else:
                    sms.delete()
                    import secrets
                    token = secrets.token_urlsafe(32)
                    user = User.objects.get(phone=phone)
                    user.reset_token = token
                    user.save()
                    request.session['recovery_token'] = token
                    request.session['recovery_step'] = 3
            except SmsCode.DoesNotExist:
                messages.error(request, 'Код не найден')
        elif action == 'reset_password':
            token = request.session.get('recovery_token', '')
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')
            if len(password) < 6:
                messages.error(request, 'Пароль минимум 6 символов')
            elif password != password2:
                messages.error(request, 'Пароли не совпадают')
            else:
                try:
                    user = User.objects.get(reset_token=token)
                    user.set_password(password)
                    user.reset_token = ''
                    user.save()
                    request.session.pop('recovery_step', None)
                    request.session.pop('recovery_phone', None)
                    request.session.pop('recovery_token', None)
                    messages.success(request, 'Пароль изменён! Войдите с новым паролем.')
                    return redirect('web:login')
                except User.DoesNotExist:
                    messages.error(request, 'Недействительный токен')
    step = request.session.get('recovery_step', 1)
    return render(request, 'web/forgot_password.html', {'step': step})
