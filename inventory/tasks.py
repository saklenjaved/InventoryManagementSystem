from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_welcome_email(email):
    send_mail(
        'Welcome to IMS',
        'Thank you for registering!',
        'admin@ims.com',
        [email],
        fail_silently=False,
    )