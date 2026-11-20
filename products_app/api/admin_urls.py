from django.urls import path, include
from rest_framework.routers import DefaultRouter

from products_app.api import admin_views

router = DefaultRouter()
router.register(r"products", admin_views.AdminProductViewSet, basename="admin-product")
router.register(r"categories", admin_views.AdminCategoryViewSet, basename="admin-category")
router.register(r"orders", admin_views.AdminOrderViewSet, basename="admin-order")
router.register(r"order-statuses", admin_views.AdminOrderStatusViewSet, basename="admin-order-status")
router.register(r"quotes", admin_views.AdminQuoteViewSet, basename="admin-quote")
router.register(r"printers", admin_views.AdminPrinterViewSet, basename="admin-printer")
router.register(r"materials", admin_views.AdminMaterialViewSet, basename="admin-material")
router.register(r"print-jobs", admin_views.AdminPrintJobViewSet, basename="admin-print-job")
router.register(r"messages", admin_views.AdminContactViewSet, basename="admin-message")
router.register(r"users", admin_views.AdminUserViewSet, basename="admin-user")

urlpatterns = [
    path("auth/login/", admin_views.AdminLogin.as_view(), name="admin-login"),
    path("auth/logout/", admin_views.admin_logout, name="admin-logout"),
    path("auth/me/", admin_views.AdminMe.as_view(), name="admin-me"),
    path("", include(router.urls)),
]
