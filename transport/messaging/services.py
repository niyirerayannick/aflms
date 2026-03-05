"""
High-level messaging services.

These functions are the public API that the rest of the transport system
calls to send WhatsApp notifications (e.g. from signals, views, Celery tasks).
"""

import logging

from transport.trips.models import Trip

from .models import NotificationLog
from .twilio_client import send_whatsapp_message

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trip lifecycle notifications
# ---------------------------------------------------------------------------

def notify_driver_trip_assigned(trip: Trip) -> None:
    """Send WhatsApp to the driver when a trip is assigned."""
    phone = trip.driver.phone
    if not phone:
        logger.warning("Driver %s has no phone – skipping WhatsApp.", trip.driver)
        return

    message = (
        f"🚚 *Afrilott Transport*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"*New Trip Assigned*\n\n"
        f"📋 Order: *{trip.order_number}*\n"
        f"📍 Route: {trip.route.origin} → {trip.route.destination}\n"
        f"🚛 Vehicle: {trip.vehicle.plate_number}\n"
        f"📦 Customer: {trip.customer.company_name}\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Reply with:\n"
        f"*1* — ✅ Accept\n"
        f"*2* — ❌ Decline"
    )

    sid = send_whatsapp_message(phone, message)
    user = getattr(trip.driver, "user", None)

    NotificationLog.objects.create(
        user=user,
        phone_number=phone,
        message=message,
        status=NotificationLog.Status.SENT if sid else NotificationLog.Status.FAILED,
        twilio_sid=sid or "",
    )


def notify_customer_trip_started(trip: Trip) -> None:
    """Send WhatsApp to the customer when their shipment starts moving."""
    phone = trip.customer.phone
    if not phone:
        return

    message = (
        f"🚚 Afrilott Transport\n\n"
        f"Your shipment {trip.order_number} has started.\n"
        f"Route: {trip.route.origin} → {trip.route.destination}\n"
        f"Driver: {trip.driver.name}\n\n"
        f"We'll notify you upon delivery."
    )

    sid = send_whatsapp_message(phone, message)
    user = getattr(trip.customer, "user", None)

    NotificationLog.objects.create(
        user=user,
        phone_number=phone,
        message=message,
        status=NotificationLog.Status.SENT if sid else NotificationLog.Status.FAILED,
        twilio_sid=sid or "",
    )


def notify_customer_delivered(trip: Trip) -> None:
    """Send WhatsApp to the customer when their shipment is delivered."""
    phone = trip.customer.phone
    if not phone:
        logger.warning("Customer %s has no phone – skipping delivery WhatsApp.", trip.customer)
        return

    logger.info(
        "Sending delivery notification to customer %s (phone: %s) for trip %s",
        trip.customer.company_name, phone, trip.order_number,
    )

    message = (
        f"✅ *Afrilott Transport*\n\n"
        f"Your shipment *{trip.order_number}* has been delivered.\n"
        f"Route: {trip.route.origin} → {trip.route.destination}\n"
        f"Driver: {trip.driver.name}\n\n"
        f"Thank you for choosing Afrilott Transport! 🎉"
    )

    sid = send_whatsapp_message(phone, message)
    user = getattr(trip.customer, "user", None)

    NotificationLog.objects.create(
        user=user,
        phone_number=phone,
        message=message,
        status=NotificationLog.Status.SENT if sid else NotificationLog.Status.FAILED,
        twilio_sid=sid or "",
    )


def notify_managers_fuel_request(fuel_request) -> None:
    """Notify managers about a new fuel request."""
    from accounts.models import User

    message = (
        f"⛽ Fuel Request #{fuel_request.pk}\n"
        f"Driver: {fuel_request.driver.name}\n"
        f"Trip: {fuel_request.trip.order_number}\n"
        f"Liters: {fuel_request.liters_requested}\n\n"
        f"Reply:\n"
        f"APPROVE {fuel_request.pk}\n"
        f"REJECT {fuel_request.pk}"
    )

    managers = User.objects.filter(
        role__in=[User.Role.MANAGER, User.Role.ADMIN, User.Role.SUPERADMIN],
        is_active=True,
    ).exclude(phone="")

    for mgr in managers:
        sid = send_whatsapp_message(mgr.phone, message)
        NotificationLog.objects.create(
            user=mgr,
            phone_number=mgr.phone,
            message=message,
            status=NotificationLog.Status.SENT if sid else NotificationLog.Status.FAILED,
            twilio_sid=sid or "",
        )
