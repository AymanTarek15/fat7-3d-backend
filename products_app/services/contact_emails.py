# products_app/services/contact_emails.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_contact_notification(contact):
    """Email the store owner about a new contact-form submission.

    `contact` is a saved ContactMessage instance. Reply-To is set to the
    sender so the owner can reply directly from their inbox.
    """
    admin_email = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL
    if not admin_email:
        return  # email not configured; message is still saved in the DB

    subject = f"New contact message from {contact.name}"
    body = (
        f"Name: {contact.name}\n"
        f"Email: {contact.email}\n"
        f"Received: {contact.created:%Y-%m-%d %H:%M}\n\n"
        f"Message:\n{contact.message or '(no message)'}\n"
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_email],
        reply_to=[contact.email],
    )
    msg.send()
