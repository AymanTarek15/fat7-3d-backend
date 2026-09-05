"""Write-capable serializers for the admin dashboard.

Kept separate from the public (read-shaped) serializers in serializers.py.
"""
from django.contrib.auth.models import User

from rest_framework import serializers

from products_app.models import (
    ProductList,
    Category,
    Order,
    OrderStatus,
    ContactMessage,
)
from products_app.api.serializers import OrderItemSerializer


class AdminUserSerializer(serializers.ModelSerializer):
    # Password is write-only; hashed via set_password. Optional on update.
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "is_active", "is_staff", "is_superuser",
            "last_login", "date_joined", "password",
        ]
        read_only_fields = ["last_login", "date_joined"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError(
                {"password": "A password is required when creating a user."}
            )
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminProductSerializer(serializers.ModelSerializer):
    # Writable category by primary key; also expose its name for display.
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ProductList
        fields = [
            "id",
            "title",
            "description",
            "price",
            "image_url",
            "note",
            "category",
            "category_name",
            "on_sale",
            "active",
            "wishlist",
            "best_selling",
            "english_name_entry_only",
            "arabic_name_entry_only",
            "both_name_entry",
            "single_language_price",
            "two_language_price",
            "naskh_hadith_font",
            "babeloo_font",
            "creamy_font",
            "goudy_font",
            "avg_rating",
            "number_rating",
            "created",
        ]
        read_only_fields = ["avg_rating", "number_rating", "created"]

    def validate(self, data):
        title = data.get("title", getattr(self.instance, "title", None))
        description = data.get("description", getattr(self.instance, "description", None))
        if title and description and title == description:
            raise serializers.ValidationError(
                "Title and description should be different."
            )
        return data


class AdminCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "about", "image", "active"]


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ["id", "status"]


class AdminOrderSerializer(serializers.ModelSerializer):
    """Read-focused; only `status` is writable (owner updates fulfillment state)."""
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.PrimaryKeyRelatedField(queryset=OrderStatus.objects.all())
    status_label = serializers.CharField(source="status.status", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer_name",
            "customer_email",
            "shipping_address",
            "customer_description",
            "created_at",
            "status",
            "status_label",
            "subtotal",
            "discount_total",
            "tax_total",
            "shipping_total",
            "grand_total",
            "items",
        ]
        read_only_fields = [
            "order_number",
            "customer_name",
            "customer_email",
            "shipping_address",
            "customer_description",
            "created_at",
            "subtotal",
            "discount_total",
            "tax_total",
            "shipping_total",
            "grand_total",
        ]


class AdminContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "message", "handled", "created"]
        read_only_fields = ["id", "name", "email", "message", "created"]
