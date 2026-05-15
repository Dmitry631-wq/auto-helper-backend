"""Firebase Cloud Messaging — отправка push-уведомлений."""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_push(token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Отправляет push одному устройству по FCM-токену.
    Требует: pip install pyfcm, FCM_SERVER_KEY в .env
    """
    if not token or not settings.FCM_SERVER_KEY:
        logger.warning('FCM: токен или ключ не заданы')
        return False

    try:
        from pyfcm import FCMNotification
        push = FCMNotification(api_key=settings.FCM_SERVER_KEY)
        result = push.notify_single_device(
            registration_id=token,
            message_title=title,
            message_body=body,
            data_message=data or {},
            sound='default',
        )
        if result.get('failure'):
            logger.error(f'FCM failure: {result}')
            return False
        return True
    except Exception as e:
        logger.exception(f'FCM error: {e}')
        return False


def send_push_to_user(user, title: str, body: str, data: dict = None) -> bool:
    if not user.fcm_token:
        return False
    return send_push(user.fcm_token, title, body, data)
