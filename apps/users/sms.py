"""
SMS через SMSC.ru.
В DEBUG-режиме (SMS_DEBUG=True) код только печатается в консоль — реальная отправка не идёт.
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str) -> bool:
    """Возвращает True при успехе."""
    if getattr(settings, 'SMS_DEBUG', True):
        logger.warning(f'[SMS DEBUG] To={phone}: {message}')
        print(f'\n🔔 SMS → {phone}: {message}\n')
        return True

    try:
        resp = requests.get(
            'https://smsc.ru/sys/send.php',
            params={
                'login':   settings.SMSC_LOGIN,
                'psw':     settings.SMSC_PASSWORD,
                'phones':  phone,
                'mes':     message,
                'fmt':     1,           # JSON
                'sender':  settings.SMSC_SENDER,
                'charset': 'utf-8',
            },
            timeout=10,
        )
        data = resp.json()
        if 'error' in data:
            logger.error(f'SMSC error: {data}')
            return False
        return True
    except Exception as e:
        logger.exception(f'SMS send failed: {e}')
        return False


def send_code(phone: str, code: str) -> bool:
    message = f'Ваш код подтверждения: {code}. Не сообщайте его никому.'
    return send_sms(phone, message)
