# products_app/services/email_receipts.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_order_receipt(to_email: str, order_context: dict, bcc_admin=True):
    subject = f"Your FAT7 3D receipt — {order_context['order']['number']}"
    text_body = render_to_string("emails/receipt.txt", order_context)
    html_body = render_to_string("emails/receipt.html", order_context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,  # "FAT7 3D <fat7.3d@gmail.com>"
        to=[to_email],
        bcc=[settings.EMAIL_HOST_USER] if bcc_admin else None,
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
