"""Admin-only API for the frontend dashboard.

Every endpoint here requires a staff user (IsAdminUser). Auth is DRF token,
issued only after verifying `is_staff`. The frontend keeps that token in an
httpOnly cookie (BFF pattern) and never exposes it to the browser.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from products_app.models import ProductList, Category, Order, OrderStatus, ContactMessage
from products_app.api.admin_serializers import (
    AdminProductSerializer,
    AdminCategorySerializer,
    AdminOrderSerializer,
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
