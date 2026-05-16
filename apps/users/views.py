from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import random
import string
import requests as http_requests
from .models import SmsCode
from .serializers import UserSerializer, RegisterSerializer

User = get_user_model()


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# ── Регистрация ───────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']
        marketing_consent = serializer.validated_data.get('marketing_consent', False)

        if User.objects.filter(phone=phone).exists():
            return Response({'phone': 'Пользователь с таким номером уже существует.'},
                            status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email', '')
        user = User.objects.create_user(
            phone=phone, password=password,
            marketing_consent=marketing_consent,
            email=email,
        )
        return Response({'user': UserSerializer(user).data, 'tokens': get_tokens(user)},
                        status=status.HTTP_201_CREATED)


# ── Вход ──────────────────────────────────────────────────────
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '').strip()

        if not (phone or email) or not password:
            return Response({'detail': 'Укажите номер телефона или email и пароль.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Нормализуем телефон
        phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if phone_clean.startswith('8') and len(phone_clean) == 11:
            phone_clean = '+7' + phone_clean[1:]
        elif phone_clean.startswith('7') and len(phone_clean) == 11:
            phone_clean = '+' + phone_clean

        # Ищем пользователя — сначала по нормализованному, потом по оригинальному
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        else:
            for p in [phone_clean, phone]:
                try:
                    user = User.objects.get(phone=p)
                    break
                except User.DoesNotExist:
                    continue

        if user is None:
            return Response({'detail': 'Неверный номер телефона или пароль.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'detail': 'Неверный номер телефона или пароль.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'Аккаунт заблокирован.'},
                            status=status.HTTP_403_FORBIDDEN)

        return Response({'user': UserSerializer(user).data, 'tokens': get_tokens(user)})


# ── Профиль ───────────────────────────────────────────────────
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ── Смена пароля ──────────────────────────────────────────────
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not request.user.check_password(old_password):
            return Response({'detail': 'Неверный текущий пароль.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'detail': 'Пароль должен быть не менее 6 символов.'},
                            status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({'detail': 'Пароль изменён.'})


# ── SMS-коды ──────────────────────────────────────────────────
def _generate_code():
    return ''.join(random.choices(string.digits, k=4))


def _send_sms(phone, code):
    if getattr(settings, 'SMS_DEBUG', True):
        print(f'[SMS DEBUG] {phone}: {code}')
        return True
    try:
        import requests
        resp = requests.get('https://smsc.ru/sys/send.php', params={
            'login': settings.SMSC_LOGIN,
            'psw': settings.SMSC_PASSWORD,
            'phones': phone,
            'mes': f'Ваш код: {code}',
        }, timeout=10)
        return 'id' in resp.text.lower()
    except Exception:
        return False


class SendSmsCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone', '').strip()
        purpose = request.data.get('purpose', 'reset')

        if not phone:
            return Response({'detail': 'Укажите номер телефона.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if purpose == 'reset' and not User.objects.filter(phone=phone).exists():
            return Response({'detail': 'Пользователь не найден.'},
                            status=status.HTTP_404_NOT_FOUND)

        code = _generate_code()
        SmsCode.objects.filter(phone=phone, purpose=purpose).delete()
        SmsCode.objects.create(phone=phone, code=code, purpose=purpose)
        _send_sms(phone, code)

        return Response({'detail': 'Код отправлен.'})

class SendEmailRecoveryCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'detail': 'Укажите email.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь с таким email не найден.'},
                            status=status.HTTP_404_NOT_FOUND)

        code = _generate_code()
        SmsCode.objects.filter(phone=user.phone, purpose='reset').delete()
        SmsCode.objects.create(phone=user.phone, code=code, purpose='reset')
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if api_key:
            try:
                http_requests.post(
                    'https://api.resend.com/emails',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'from': 'Авто-помощник <noreply@auto-helper-abakan.online>',
                        'to': [email],
                        'subject': 'Восстановление доступа — Авто-помощник',
                        'text': f'Ваш код для восстановления доступа: {code}\n\nКод действителен 5 минут.',
                    },
                    timeout=10,
                )
            except Exception as e:
                print(f'[EMAIL ERROR] {e}')
        else:
            print(f'[EMAIL RECOVERY DEBUG] {email}: {code}')

        return Response({'detail': 'Код отправлен.', 'phone': user.phone})
class VerifySmsCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone   = request.data.get('phone', '').strip()
        code    = request.data.get('code', '').strip()
        purpose = request.data.get('purpose', 'reset')

        try:
            sms = SmsCode.objects.filter(phone=phone, purpose=purpose).latest('created_at')
        except SmsCode.DoesNotExist:
            return Response({'detail': 'Код не найден.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if sms.is_expired():
            return Response({'detail': 'Код истёк. Запросите новый.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if sms.code != code:
            return Response({'detail': 'Неверный код.'},
                            status=status.HTTP_400_BAD_REQUEST)

        sms.delete()

        # Если сброс пароля — возвращаем reset_token
        if purpose == 'reset':
            import secrets
            token = secrets.token_urlsafe(32)
            try:
                user = User.objects.get(phone=phone)
                user.reset_token = token
                user.save()
            except User.DoesNotExist:
                pass
            return Response({'detail': 'Код подтверждён.', 'reset_token': token})

        return Response({'detail': 'Код подтверждён.'})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        reset_token = request.data.get('reset_token', '').strip()
        new_password = request.data.get('new_password', '').strip()

        try:
            user = User.objects.get(reset_token=reset_token)
        except User.DoesNotExist:
            return Response({'detail': 'Недействительный токен.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'detail': 'Пароль должен быть не менее 6 символов.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.reset_token = ''
        user.save()
        return Response({'detail': 'Пароль изменён.'})


# ── Токен рефреш ──────────────────────────────────────────────
class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh', '')
        try:
            token = RefreshToken(refresh_token)
            return Response({'access': str(token.access_token)})
        except TokenError:
            return Response({'detail': 'Токен недействителен или истёк.'},
                            status=status.HTTP_401_UNAUTHORIZED)


# ── FCM токен ──────────────────────────────────────────────────
class SaveFcmTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token', '')
        if token:
            request.user.fcm_token = token
            request.user.save()
        return Response({'detail': 'OK'})


# ── Email верификация ──────────────────────────────────────────
class SendEmailCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'detail': 'Укажите email.'},
                            status=status.HTTP_400_BAD_REQUEST)

        code = _generate_code()
        SmsCode.objects.filter(phone=request.user.phone, purpose='email').delete()
        SmsCode.objects.create(phone=request.user.phone, code=code, purpose='email')

        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if api_key:
            try:
                http_requests.post(
                    'https://api.resend.com/emails',
                    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                    json={
                        'from': 'Авто-помощник <noreply@auto-helper-abakan.online>',
                        'to': [email],
                        'subject': 'Подтверждение email — Авто-помощник',
                        'text': f'Ваш код подтверждения: {code}',
                    },
                    timeout=10,
                )
            except Exception as e:
                print(f'[EMAIL ERROR] {e}')
        else:
            print(f'[EMAIL DEBUG] {email}: {code}')

        return Response({'detail': 'Код отправлен.'})


class VerifyEmailCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email', '').strip()
        code  = request.data.get('code', '').strip()

        try:
            sms = SmsCode.objects.filter(
                phone=request.user.phone, purpose='email').latest('created_at')
        except SmsCode.DoesNotExist:
            return Response({'detail': 'Код не найден.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if sms.is_expired():
            return Response({'detail': 'Код истёк.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if sms.code != code:
            return Response({'detail': 'Неверный код.'},
                            status=status.HTTP_400_BAD_REQUEST)

        sms.delete()
        request.user.email = email
        request.user.save()
        return Response({'detail': 'Email подтверждён.'})


# ── Вопрос в поддержку ────────────────────────────────────────
class AskQuestionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        question = request.data.get('question', '').strip()
        email    = request.data.get('email', '').strip()
        phone    = request.data.get('phone', '').strip()

        if not question:
            return Response({'detail': 'Введите вопрос.'},
                            status=status.HTTP_400_BAD_REQUEST)

        sender = email or phone or 'Аноним'
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if api_key:
            try:
                http_requests.post(
                    'https://api.resend.com/emails',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'from': 'Авто-помощник <noreply@auto-helper-abakan.online>',
                        'to': ['mikshindima89@gmail.com'],
                        'subject': f'Вопрос от {sender} — Авто-помощник',
                        'text': f'От: {sender}\n\n{question}',
                    },
                    timeout=10,
                )
            except Exception as e:
                print(f'[EMAIL ERROR] {e}')

        return Response({'detail': 'Вопрос отправлен.'})


# ── Удаление аккаунта ──────────────────────────────────────────
class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'detail': 'Аккаунт удалён.'})
class UnlockAccountView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        secret = request.data.get('secret', '')
        if secret != 'auto-helper-unlock-2024':
            return Response({'detail': 'Forbidden'}, status=403)
        phone = request.data.get('phone', '').strip()
        if not phone:
            # Показываем всех пользователей
            users = list(User.objects.values('id', 'phone', 'email', 'is_active', 'first_name', 'last_name'))
            return Response({'users': users})
        # Разблокируем по телефону или email
        user = User.objects.filter(phone=phone).first() or User.objects.filter(email=phone).first()
        if not user:
            return Response({'detail': 'Не найден'}, status=404)
        user.is_active = True
        user.save()
        return Response({'detail': f'Разблокирован: {user.phone}'})