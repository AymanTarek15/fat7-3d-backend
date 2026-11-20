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
    Quote,
    QuoteItem,
    Printer,
    Material,
    PrintJob,
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
    """Read-focused; `status`, `payment_status` and `amount_paid` are writable
    (the owner updates fulfillment and payment state from the admin)."""
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.PrimaryKeyRelatedField(queryset=OrderStatus.objects.all())
    status_label = serializers.CharField(source="status.status", read_only=True)
    payment_status_label = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )

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
            "payment_status",
            "payment_status_label",
            "amount_paid",
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

class AdminQuoteItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    process_label = serializers.CharField(source="get_process_display", read_only=True)

    class Meta:
        model = QuoteItem
        fields = [
            "id", "name", "spec", "process", "process_label",
            "quantity", "unit_price", "line_total",
        ]


class AdminQuoteSerializer(serializers.ModelSerializer):
    """Quotes with their line items. Items are written inline so the admin can
    save a quote and its lines in one request."""

    items = AdminQuoteItemSerializer(many=True, required=False)

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    service_label = serializers.CharField(source="get_service_display", read_only=True)

    # Derived on the model, exposed read-only so the numbers can never drift
    # apart from the line items they come from.
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cost_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    margin_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    margin_percent = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True, allow_null=True
    )

    converted_order_number = serializers.CharField(
        source="converted_order.order_number", read_only=True, default=None
    )

    class Meta:
        model = Quote
        fields = [
            "id", "quote_number",
            "customer_name", "customer_email", "customer_company",
            "service", "service_label", "status", "status_label",
            "created_at", "valid_until", "source",
            "customer_notes", "terms",
            "materials_cost", "machining_cost", "additional_cost",
            "subtotal", "cost_total", "margin_amount", "margin_percent",
            "converted_order", "converted_order_number",
            "items",
        ]
        read_only_fields = ["quote_number", "created_at", "converted_order"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        quote = Quote.objects.create(**validated_data)
        for item in items:
            QuoteItem.objects.create(quote=quote, **item)
        return quote

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Items are replaced wholesale: the admin edits the whole line set at
        # once, and diffing by id would silently keep rows the user deleted.
        if items is not None:
            instance.items.all().delete()
            for item in items:
                QuoteItem.objects.create(quote=instance, **item)

        return instance


class AdminPrinterSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    current_job = serializers.SerializerMethodField()

    class Meta:
        model = Printer
        fields = ["id", "name", "model_name", "status", "status_label", "notes", "active", "current_job"]

    def get_current_job(self, obj):
        job = obj.jobs.filter(status=PrintJob.STATUS_PRINTING).first()
        if not job:
            return None
        return {
            "id": job.id,
            "job_number": job.job_number,
            "file_name": job.file_name,
            "progress_percent": job.progress_percent,
            "elapsed_minutes": job.elapsed_minutes,
            "estimated_minutes": job.estimated_minutes,
        }


class AdminMaterialSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source="get_material_type_display", read_only=True)

    class Meta:
        model = Material
        fields = [
            "id", "name", "material_type", "type_label",
            "color", "color_hex", "stock_grams", "cost_per_gram",
        ]


class AdminPrintJobSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    post_stage_label = serializers.CharField(source="get_post_stage_display", read_only=True)
    printer_name = serializers.CharField(source="printer.name", read_only=True, default=None)
    material_name = serializers.CharField(source="material.name", read_only=True, default=None)
    material_type = serializers.CharField(source="material.material_type", read_only=True, default=None)
    material_hex = serializers.CharField(source="material.color_hex", read_only=True, default=None)
    order_number = serializers.CharField(source="order.order_number", read_only=True, default=None)
    quote_number = serializers.CharField(source="quote.quote_number", read_only=True, default=None)

    # Derived, read-only: estimated from the planned duration, not telemetry.
    progress_percent = serializers.IntegerField(read_only=True)
    elapsed_minutes = serializers.IntegerField(read_only=True)
    remaining_minutes = serializers.IntegerField(read_only=True)
    estimated_finish = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PrintJob
        fields = [
            "id", "job_number", "file_name",
            "printer", "printer_name",
            "material", "material_name", "material_type", "material_hex",
            "quantity", "layer_height", "infill_percent",
            "estimated_minutes", "filament_estimated_g", "filament_used_g",
            "status", "status_label", "post_stage", "post_stage_label",
            "started_at", "completed_at", "failure_reason",
            "order", "order_number", "quote", "quote_number", "note",
            "created_at",
            "progress_percent", "elapsed_minutes", "remaining_minutes", "estimated_finish",
        ]
        read_only_fields = ["job_number", "created_at"]
