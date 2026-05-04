import logging
import threading

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task
def send_signup_notification_email(email, username):
    subject = 'Welcome to Inventory Management System'
    message = (
        f'Hi {username},\n\n'
        'Your account was created successfully.\n'
        'Thanks for signing up.'
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return f'Notification sent for {email}'


def _deliver_signup_email(email: str, username: str) -> None:
    try:
        if settings.CELERY_TASK_ALWAYS_EAGER:
            send_signup_notification_email(email=email, username=username)
            return
        try:
            send_signup_notification_email.delay(email=email, username=username)
        except Exception as exc:
            logger.warning(
                'Celery broker unavailable (%s); sending signup email synchronously.',
                exc,
            )
            send_signup_notification_email(email=email, username=username)
    except Exception:
        logger.exception('Signup welcome email skipped for %s', email)


def enqueue_signup_notification(email: str, username: str) -> None:
   
    threading.Thread(
        target=_deliver_signup_email,
        args=(email, username),
        daemon=True,
    ).start()
