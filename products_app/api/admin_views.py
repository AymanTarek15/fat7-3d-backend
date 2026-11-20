"""Admin-only API for the frontend dashboard.

Every endpoint here requires a staff user (IsAdminUser). Auth is DRF token,
issued only after verifying `is_staff`. The frontend keeps that token in an
httpOnly cookie (BFF pattern) and never exposes it to the browser.
"""
from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from products_app.models import (
    ProductList,
    Category,
    Order,
    OrderStatus,
    ContactMessage,
    Quote,
    Printer,
    Material,
    PrintJob,
)
from products_app.api.admin_serializers import (
    AdminProductSerializer,
    AdminCategorySerializer,
    AdminOrderSerializer,
    AdminQuoteSerializer,
    AdminPrinterSerializer,
    AdminMaterialSerializer,
    AdminPrintJobSerializer,
    OrderStatusSerializer,
    AdminContactSerializer,
    AdminUserSerializer,
)


class IsSuperUser(BasePermission):
    """User management is restricted to superusers (not just staff)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class AdminLogin(APIView):
    """Authenticate a staff user and return a token. Throttled against brute force."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=username, password=password)

        # Generic message — do not reveal whether the user exists or lacks staff.
        if user is None or not user.is_staff:
            return Response(
                {"detail": "Invalid credentials or not authorized."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username})


class AdminMe(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        u = request.user
        return Response(
            {"username": u.username, "is_staff": u.is_staff, "is_superuser": u.is_superuser}
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ProductList.objects.select_related("category").order_by("-created")
    serializer_class = AdminProductSerializer


class AdminCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Category.objects.all().order_by("name")
    serializer_class = AdminCategorySerializer


class AdminOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "patch", "head", "options"]  # no create/delete of orders here
    queryset = Order.objects.prefetch_related("items", "items__product").order_by("-created_at")
    serializer_class = AdminOrderSerializer


class AdminOrderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of statuses to populate the order status dropdown."""
    permission_classes = [IsAdminUser]
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer


class AdminContactViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = ContactMessage.objects.all().order_by("-created")
    serializer_class = AdminContactSerializer


class AdminUserViewSet(viewsets.ModelViewSet):
    """Superuser-only user management with self-lockout protection."""
    permission_classes = [IsSuperUser]
    queryset = User.objects.all().order_by("username")
    serializer_class = AdminUserSerializer

    def _guard_self(self, instance, data):
        """Prevent an admin from locking themselves out."""
        if instance.pk != self.request.user.pk:
            return
        for field, label in [
            ("is_superuser", "superuser status"),
            ("is_staff", "staff access"),
            ("is_active", "active status"),
        ]:
            if field in data and not data[field]:
                raise ValidationError(f"You cannot remove your own {label}.")

    def perform_update(self, serializer):
        self._guard_self(serializer.instance, serializer.validated_data)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError("You cannot delete your own account.")
        instance.delete()

class AdminQuoteViewSet(viewsets.ModelViewSet):
    """Quotes, with an action to turn an accepted one into a real Order."""

    queryset = Quote.objects.all().prefetch_related("items")
    serializer_class = AdminQuoteSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"], url_path="convert")
    def convert(self, request, pk=None):
        quote = self.get_object()

        if quote.converted_order_id:
            raise ValidationError(
                {"detail": f"Already converted to order {quote.converted_order.order_number}."}
            )

        total = quote.subtotal
        if not total:
            raise ValidationError({"detail": "Add at least one line item before converting."})

        first_status = OrderStatus.objects.order_by("id").first()
        if first_status is None:
            raise ValidationError({"detail": "No order statuses are configured."})

        # OrderItem.product is a required FK to the catalogue, and quote lines
        # are free text, so the breakdown is carried over as a description
        # rather than invented catalogue rows.
        lines = "\n".join(
            f"- {i.name}"
            + (f" ({i.spec})" if i.spec else "")
            + f" x{i.quantity} @ {i.unit_price} = {i.line_total}"
            for i in quote.items.all()
        )
        description = f"Converted from quote {quote.quote_number}.\n{lines}"
        if quote.customer_notes:
            description += f"\n\nCustomer notes:\n{quote.customer_notes}"

        order = Order.objects.create(
            customer_name=quote.customer_name,
            customer_email=quote.customer_email or "",
            shipping_address="",
            customer_description=description[:500],
            status=first_status,
            subtotal=total,
            discount_total=0,
            tax_total=0,
            shipping_total=0,
            grand_total=total,
        )

        quote.converted_order = order
        quote.status = Quote.STATUS_ACCEPTED
        quote.save()

        return Response(self.get_serializer(quote).data, status=status.HTTP_201_CREATED)


class AdminPrinterViewSet(viewsets.ModelViewSet):
    queryset = Printer.objects.all().prefetch_related("jobs")
    serializer_class = AdminPrinterSerializer
    permission_classes = [IsAdminUser]


class AdminMaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = AdminMaterialSerializer
    permission_classes = [IsAdminUser]


class AdminPrintJobViewSet(viewsets.ModelViewSet):
    queryset = PrintJob.objects.all().select_related("printer", "material", "order", "quote")
    serializer_class = AdminPrintJobSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=["post"], url_path="advance")
    def advance(self, request, pk=None):
        """Move a job to a new status, keeping the side effects consistent.

        Starting a print stamps started_at and marks the printer busy;
        finishing stamps completed_at, deducts the filament from stock and
        frees the printer. Doing this server-side means the board cannot drift
        out of step with the printers and the material counts.
        """
        job = self.get_object()
        target = request.data.get("status")

        valid = dict(PrintJob.STATUS_CHOICES)
        if target not in valid:
            raise ValidationError({"detail": f"Unknown status '{target}'."})

        from django.utils import timezone

        if target == PrintJob.STATUS_PRINTING:
            if job.printer is None:
                raise ValidationError({"detail": "Assign a printer before starting the job."})
            job.started_at = job.started_at or timezone.now()
            job.completed_at = None
            job.failure_reason = ""
            job.printer.status = Printer.STATUS_PRINTING
            job.printer.save()

        elif target == PrintJob.STATUS_POST:
            job.completed_at = job.completed_at or timezone.now()
            job.post_stage = request.data.get("post_stage") or job.post_stage or "supports"
            if job.printer:
                job.printer.status = Printer.STATUS_IDLE
                job.printer.save()

        elif target == PrintJob.STATUS_COMPLETED:
            job.completed_at = job.completed_at or timezone.now()
            if not job.filament_used_g:
                job.filament_used_g = job.filament_estimated_g
            if job.material and job.filament_used_g:
                job.material.stock_grams = max(
                    Decimal("0"), job.material.stock_grams - job.filament_used_g
                )
                job.material.save()
            if job.printer:
                job.printer.status = Printer.STATUS_IDLE
                job.printer.save()

        elif target == PrintJob.STATUS_FAILED:
            job.failure_reason = request.data.get("failure_reason") or job.failure_reason or "Unspecified"
            job.completed_at = timezone.now()
            if job.printer:
                job.printer.status = Printer.STATUS_IDLE
                job.printer.save()

        elif target == PrintJob.STATUS_QUEUED:
            job.started_at = None
            job.completed_at = None
            job.failure_reason = ""
            job.post_stage = ""
            if job.printer and job.printer.status == Printer.STATUS_PRINTING:
                job.printer.status = Printer.STATUS_IDLE
                job.printer.save()

        job.status = target
        job.save()
        return Response(self.get_serializer(job).data)
