import logging
from datetime import timedelta

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User, UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def sync_user_role_to_module(sender, instance, **kwargs):
    """
    When a user is saved with role 'driver', ensure a Driver record exists.
    When a user is saved with role 'client', ensure a Customer record exists.
    Checks by both user FK and email to prevent duplicates.
    """
    # Prevent re-entrant signals (driver.save() / customer.save() won't loop)
    if getattr(instance, '_syncing_role', False):
        return
    instance._syncing_role = True

    try:
        if instance.role == User.Role.DRIVER:
            _ensure_driver_exists(instance)
        elif instance.role == User.Role.CLIENT:
            _ensure_customer_exists(instance)
    finally:
        instance._syncing_role = False


def _ensure_driver_exists(user):
    """Create or sync a Driver record for this user."""
    try:
        from transport.drivers.models import Driver

        # Check if a Driver already exists linked to this user
        existing = Driver.objects.filter(user=user).first()
        if existing:
            changed = False
            if existing.name != user.full_name:
                existing.name = user.full_name
                changed = True
            if existing.email != user.email:
                existing.email = user.email
                changed = True
            if user.phone and existing.phone != user.phone:
                existing.phone = user.phone
                changed = True
            if changed:
                existing.save()
            return

        # Check if a Driver exists with same email but no user linked yet
        # (created by the driver form before the user was created)
        unlinked = Driver.objects.filter(email__iexact=user.email, user__isnull=True).first()
        if unlinked:
            unlinked.user = user
            unlinked.name = user.full_name
            if user.phone:
                unlinked.phone = user.phone
            unlinked.save()
            logger.info("Linked existing Driver record to user %s", user.email)
            return

        # No existing driver at all — create one
        Driver.objects.create(
            user=user,
            name=user.full_name,
            email=user.email,
            phone=user.phone or '',
            license_number=f'PENDING-{str(user.pk)[:8]}',
            license_expiry=timezone.now().date() + timedelta(days=365),
            status=Driver.DriverStatus.AVAILABLE,
        )
        logger.info("Auto-created Driver record for user %s", user.email)
    except Exception as e:
        logger.error("Could not sync Driver for user %s: %s", user.email, e, exc_info=True)


def _ensure_customer_exists(user):
    """Create or sync a Customer record for this user."""
    try:
        from transport.customers.models import Customer

        # Check if a Customer already exists linked to this user
        existing = Customer.objects.filter(user=user).first()
        if existing:
            changed = False
            if existing.contact_person != user.full_name:
                existing.contact_person = user.full_name
                changed = True
            if existing.email != user.email:
                existing.email = user.email
                changed = True
            if user.phone and existing.phone != user.phone:
                existing.phone = user.phone
                changed = True
            if changed:
                existing.save()
            return

        # Check if a Customer exists with same email but no user linked
        unlinked = Customer.objects.filter(email__iexact=user.email, user__isnull=True).first()
        if unlinked:
            unlinked.user = user
            unlinked.contact_person = user.full_name
            if user.phone:
                unlinked.phone = user.phone
            unlinked.save()
            logger.info("Linked existing Customer record to user %s", user.email)
            return

        # No existing customer — create one
        Customer.objects.create(
            user=user,
            company_name=user.full_name,
            contact_person=user.full_name,
            email=user.email,
            phone=user.phone or '',
            status=Customer.CustomerStatus.ACTIVE,
        )
        logger.info("Auto-created Customer record for user %s", user.email)
    except Exception as e:
        logger.error("Could not sync Customer for user %s: %s", user.email, e, exc_info=True)


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
