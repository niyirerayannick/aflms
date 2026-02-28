import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(
        "User logged in: email=%s role=%s ip=%s",
        user.email,
        user.role,
        request.META.get("REMOTE_ADDR"),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is None:
        return
    logger.info(
        "User logged out: email=%s role=%s ip=%s",
        user.email,
        user.role,
        request.META.get("REMOTE_ADDR") if request else None,
    )
