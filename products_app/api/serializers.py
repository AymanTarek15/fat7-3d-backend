from rest_framework import serializers
from products_app.models import Review,Category, ProductList,ProductImage,SeasonChange,Order,OrderItem,OrderStatus,Colour,ProductColour,ContactMessage
from decimal import Decimal
from django.db import transaction


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "message", "created"]
        read_only_fields = ["id", "created"]

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter your name.")
        return value

    def validate_message(self, value):
        return value.strip()



class ProductColourSerializer(serializers.ModelSerializer):
    colour = serializers.StringRelatedField()  # "Red"
    class Meta:
        model = ProductColour
        fields = ["id", "colour", "image_url",  "active"]



class ColorNameField(serializers.Field):
    def to_internal_value(self, value):
        if value in (None, ""): return None
        return str(value).strip()

    def to_representation(self, obj):
        return obj.colour.name if obj else None


class ImageSerializer(serializers.ModelSerializer):
  
  product=serializers.StringRelatedField()
  
  class Meta:
    model=ProductImage
    fields="__all__"
    # exclude=('watchlist',)
    
class ReviewSerializer(serializers.ModelSerializer):
  
  review_user=serializers.StringRelatedField(read_only=True)
  
  class Meta:
    model=Review
    fields="__all__"
    
class SeasonChangeSerializer(serializers.ModelSerializer):
  
  # review_user=serializers.StringRelatedField(read_only=True)
  
  class Meta:
    model=SeasonChange
    fields="__all__"

class ProductListSerializer(serializers.ModelSerializer):
  images=ImageSerializer(many=True, read_only=True)
  image_items = ImageSerializer(many=True, write_only=True, required=False)
  # len_name=serializers.SerializerMethodField()
  category=serializers.CharField(source='category.name')
  # colour=serializers.CharField(source='colour.name')
  color_options = ProductColourSerializer(many=True, read_only=True)
  reviews=ReviewSerializer(many=True,read_only=True)   # to add reviews to the movies
  
  class Meta:
    model=ProductList
    fields="__all__"
    
  def validate(self, data):
    if data['title']==data['description']:
      raise serializers.ValidationError("Title and Description should be different!")
    else:
      return data
    # return super().validate(data)
  
  def validate_name(self, value):
    
    if len(value) < 2:
      raise serializers.ValidationError("Name is too short!")
    else:
      return value
    
    
class CategorySerializer(serializers.ModelSerializer):
  product=ProductListSerializer(many=True, read_only=True)
  
  class Meta:
    model=Category
    fields="__all__"
    
    
    
# New insertions for orders



# class OrderItemCreateSerializer(serializers.ModelSerializer):
#     # Accept product by id from the client
#     product_id = serializers.PrimaryKeyRelatedField(
#         source="product", queryset=ProductList.objects.all(), write_only=True
#     )
    
#     color = serializers.SlugRelatedField(                
#         slug_field="name", queryset=Colour.objects.all(), required=False
#     )
#     # expose product basics back to client
#     product = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = OrderItem
#         fields = [
#             "product_id",
#             "product",
#             "color",
#             "personalization_name",   
#             "unit_price",
#             "quantity",
#             "discount",
#             "tax",
#             "line_total",
#         ]
#         read_only_fields = ["line_total"]

#     def validate(self, data):
#         qty = data.get("quantity") or 0
#         if qty <= 0:
#             raise serializers.ValidationError("Quantity must be > 0.")
#         # Optionally verify unit_price with DB to prevent tampering:
#         product = data["product"]
#         db_price = Decimal(str(getattr(product, "price", 0)))
#         sent_price = Decimal(str(data.get("unit_price") or 0))
#         # Allow using the server price; or allow difference if you have discounts.
#         if sent_price <= 0:
#             data["unit_price"] = db_price
#         return data


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    color = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "color",
            "personalization_option",
            "personalization_name_en",
            "personalization_name_ar",
            "personalization_font_en",
            "personalization_font_ar",
            "unit_price",
            "quantity",
            "discount",
            "tax",
            "line_total",
        ]
        
    def get_color(self, obj):
        return obj.color_option.colour.name if obj.color_option else None


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product", queryset=ProductList.objects.all(), write_only=True
    )
    # send either color name ("Red") OR color_option_id (advanced clients)
    color = ColorNameField(required=False)  # name like "Red"
    color_option_id = serializers.PrimaryKeyRelatedField(
        source="color_option", queryset=ProductColour.objects.all(),
        required=False, write_only=True
    )

    product = serializers.StringRelatedField(read_only=True)
    color_option = serializers.SerializerMethodField(read_only=True)  # expose selected option

    class Meta:
        model = OrderItem
        fields = [
            "product_id", "product",
            "color", "color_option_id", "color_option",
            "personalization_option",
            "personalization_name_en",
            "personalization_name_ar",
            "personalization_font_en", 
            "personalization_font_ar",
            "unit_price", "quantity", "discount", "tax", "line_total",
        ]
        read_only_fields = ["line_total"]

    def get_color_option(self, obj):
        if not obj.color_option: return None
        return {
            "id": obj.color_option.id,
            "colour": obj.color_option.colour.name,
            "image_url": obj.color_option.image_url,
            
        }

    def validate(self, data):
        qty = int(data.get("quantity") or 0)
        if qty <= 0:
            raise serializers.ValidationError("Quantity must be > 0.")

        product = data["product"]

        # If client gave color_option_id, ensure it belongs to this product
        color_opt = data.get("color_option")
        if color_opt and color_opt.product_id != product.id:
            raise serializers.ValidationError("Color option does not belong to this product.")

        # If client gave color name, resolve it to a ProductColour
        color_name = data.pop("color", None)
        if not color_opt and color_name:
            try:
                data["color_option"] = ProductColour.objects.get(
                    product=product, colour__name__iexact=color_name
                )
            except ProductColour.DoesNotExist:
                raise serializers.ValidationError(
                    f"Color '{color_name}' is not available for '{product.title}'."
                )

        # Set price if missing/<=0: base + delta
        sent_price = Decimal(str(data.get("unit_price") or 0))
        if sent_price <= 0:
            data["unit_price"] = Decimal(str(product.price))

        return data



class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    
    
    
    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "customer_email",
            "shipping_address",
            "customer_description",
            "subtotal",
            "discount_total",
            "tax_total",
            "shipping_total",
            "grand_total",
            "items",
        ]
        read_only_fields = ["subtotal", "discount_total", "tax_total", "grand_total"]
        
        
        
        
        
    
    def _get_pending_status(self):
        # Your model has FK to OrderStatus but default="pending" (string) is not ideal.
        # Safer: look up the "pending" row or pick the first status.
        try:
            return OrderStatus.objects.get(status__iexact="pending")
        except OrderStatus.DoesNotExist:
            return OrderStatus.objects.create(status='pending')

    @transaction.atomic
    def create(self, validated):
        items_data = validated.pop("items", [])
        # Set/ensure status (since default="pending" on FK is unsafe)
        order = Order(**validated)
        if not order.status_id:
            order.status = self._get_pending_status()
        order.subtotal = Decimal("0.00")
        order.discount_total = Decimal("0.00")
        order.tax_total = Decimal("0.00")
        order.shipping_total = order.shipping_total or Decimal("0.00")  # client may send 0
        order.grand_total = Decimal("0.00")
        order.save()

        # Build items and totals
        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        tax_total = Decimal("0.00")

        for row in items_data:
            product = row["product"]
            qty = int(row["quantity"])
            unit_price = Decimal(str(row["unit_price"]))
            discount = Decimal(str(row.get("discount", 0)))
            tax = Decimal(str(row.get("tax", 0)))
            line_total = unit_price * qty - discount + tax

            item = OrderItem.objects.create(
                order=order,
                product=product,
                color_option=row.get("color_option"),
                # personalization_name=row.get("personalization_name"),
                personalization_option=row.get("personalization_option", "none"),
                personalization_name_en=row.get("personalization_name_en") or "",
                personalization_name_ar=row.get("personalization_name_ar") or "",
                
                # to add fonts
                personalization_font_en=row.get("personalization_font_en") or None,
                personalization_font_ar=row.get("personalization_font_ar") or None,
                unit_price=unit_price,
                quantity=qty,
                discount=discount,
                tax=tax,
                line_total=line_total,
            )

            subtotal += unit_price * qty
            discount_total += discount
            tax_total += tax

        order.subtotal = subtotal
        order.discount_total = discount_total
        order.tax_total = tax_total
        order.grand_total = subtotal - discount_total + tax_total + order.shipping_total
        order.save()

        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "customer_email",
            "shipping_address",
            "customer_description",
            "created_at",
            "status",
            "subtotal",
            "discount_total",
            "tax_total",
            "shipping_total",
            "grand_total",
            "items",
        ]