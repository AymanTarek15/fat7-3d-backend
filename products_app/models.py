from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from django.contrib.auth.models import User
import uuid
# Create your models here.


class Category(models.Model):
  name=models.CharField(max_length=30)
  about=models.CharField(max_length=150)
  active=models.BooleanField(default=True)
  image=models.URLField(max_length=1000)
  # website=models.URLField(max_length=100)
  class Meta:
    verbose_name_plural = "Categories"
  def __str__(self):
    return self.name
  
class SeasonChange(models.Model):
  name=models.CharField(max_length=30)
  about=models.CharField(max_length=150)
  image=models.URLField(max_length=1000)
  active=models.BooleanField(default=False)
  
  def __str__(self):
    return self.name
  
class Colour(models.Model):
  name=models.CharField(max_length=30)
  # about=models.CharField(max_length=150)
  # image=models.URLField(max_length=100)
  
  def __str__(self):
    return self.name

class ProductList(models.Model):
  title=models.CharField(max_length=50)
  description=models.CharField(max_length=200)
  price=models.FloatField()
  image_url=models.URLField(max_length=1000)
  note=models.CharField(null=True, blank=True)
  # platform=models.ForeignKey(StreamPlatform, on_delete=models.CASCADE,related_name="watchlist")
  on_sale=models.BooleanField(default=False)
  active=models.BooleanField(default=True)
  wishlist=models.BooleanField(default=False)
  best_selling=models.BooleanField(default=False)
  english_name_entry_only=models.BooleanField(default=False)
  arabic_name_entry_only=models.BooleanField(default=False)
  both_name_entry=models.BooleanField(default=False)
  single_language_price=models.FloatField(default=0)
  two_language_price=models.FloatField(default=0)
  naskh_hadith_font=models.BooleanField(default=False)
  babeloo_font=models.BooleanField(default=False)
  creamy_font=models.BooleanField(default=False)
  goudy_font=models.BooleanField(default=False)
  # colour=models.ForeignKey(Colour,on_delete=models.CASCADE,related_name='colour')
  category=models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category')
  created=models.DateTimeField(auto_now_add=True)
  avg_rating=models.FloatField(default=0)
  number_rating=models.IntegerField(default=0)
  
  def __str__(self):
    return self.title
  
class ProductColour(models.Model):
    product = models.ForeignKey(ProductList, on_delete=models.CASCADE, related_name="color_options")
    colour  = models.ForeignKey(Colour, on_delete=models.PROTECT, related_name="product_options")
    image_url = models.URLField(max_length=1000)  # image for THIS color option
  
    
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "colour"], name="uniq_product_colour")
        ]

    def __str__(self):
        return f"{self.product.title} - {self.colour.name}"
  
class Review(models.Model):
  review_user=models.ForeignKey(User, on_delete=models.CASCADE)
  rating=models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
  description=models.CharField(max_length=200, null=True)
  productlist=models.ForeignKey(ProductList,on_delete=models.CASCADE,related_name="reviews",)
  active=models.BooleanField(default=True)
  created=models.DateTimeField(auto_now_add=True)
  update=models.DateTimeField(auto_now=True)

  
  def __str__(self):
    return str(self.rating) + " | "+ self.productlist.title
  
  
class ProductImage(models.Model):
  name=models.CharField(max_length=200)
  description=models.CharField(max_length=500, null=True, blank=True)
  image_url=models.URLField( max_length=1000 )
  product=models.ForeignKey(ProductList,on_delete=models.CASCADE,related_name="images",)
  active=models.BooleanField(default=True)
  created=models.DateTimeField(auto_now_add=True)
  update=models.DateTimeField(auto_now=True)

  
  def __str__(self):
    return str(self.name) + " | " + str(self.product)
  
  
  
class OrderStatus(models.Model):
  status=models.CharField(max_length=20)
  
  class Meta:
    verbose_name_plural="Order Status"
    
  def __str__(self):
    return str(self.status)
  
class Order(models.Model):
    # customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_number = models.CharField(
        max_length=20, unique=True, editable=False
    )
    customer_name=models.CharField(max_length=200)
    customer_email=models.EmailField(max_length=100)
    shipping_address=models.CharField(max_length=500, null=True)
    customer_description=models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey(OrderStatus , on_delete=models.PROTECT, related_name='order_status')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)   # optional denormalized
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Example pattern: FAT7-2025100001
            from datetime import datetime
            prefix = datetime.now().strftime("%Y%m")
            unique_part = str(uuid.uuid4().int)[:6]
            self.order_number = f"ORD-{prefix}-{unique_part}"
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.order_number} | {self.status}"
    
  
# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
#     product = models.ForeignKey(ProductList, on_delete=models.PROTECT)
#     personalization_name = models.CharField(max_length=100, blank=True, null=True)
#     color=models.ForeignKey(Colour, on_delete=models.PROTECT, null=True, blank=True)
#     # name_snapshot = models.CharField(max_length=255)  # product name at purchase time
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # price at purchase
#     quantity = models.PositiveIntegerField()
#     discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # per line
#     tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     line_total = models.DecimalField(max_digits=12, decimal_places=2)
    
#     def __str__(self):
#         return str(self.product)+' | '  + self.order.order_number+ ' (x'+ str(self.quantity)+')'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(ProductList, on_delete=models.PROTECT)
    color_option = models.ForeignKey(ProductColour, on_delete=models.PROTECT, null=True, blank=True)
    personalization_option = models.CharField(
        max_length=10, default="none", choices=[
            ("none", "None"),
            ("en", "English only"),
            ("ar", "Arabic only"),
            ("both", "English + Arabic"),
        ]
    )
    personalization_name_en = models.CharField(max_length=100, blank=True, null=True)
    personalization_name_ar = models.CharField(max_length=100, blank=True, null=True)
    
    personalization_font_en = models.CharField(max_length=30, blank=True, null=True) 
    personalization_font_ar = models.CharField(max_length=30, blank=True, null=True)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # final price used
    quantity = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        co = f" - {self.color_option.colour.name}" if self.color_option else ""
        return f"{self.product}{co} | {self.order.order_number} (x{self.quantity})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    message = models.TextField(max_length=2000, blank=True)
    handled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} <{self.email}> | {self.created:%Y-%m-%d %H:%M}"
