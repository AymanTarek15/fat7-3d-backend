from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from django.contrib.auth.models import User
import uuid
from decimal import Decimal
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

    # --- Payment tracking -------------------------------------------------
    # Both fields carry defaults so the migration leaves existing orders
    # untouched; they start as "unpaid" with nothing recorded against them,
    # which is accurate rather than assumed.
    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PARTIAL = "partial"
    PAYMENT_PAID = "paid"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PARTIAL, "Partially Paid"),
        (PAYMENT_PAID, "Paid"),
    ]
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_UNPAID,
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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

class Quote(models.Model):
    """A price request that can be priced, sent, and converted into an Order."""

    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    SERVICE_CHOICES = [
        ("3d_print", "3D Print"),
        ("cnc", "CNC"),
        ("pcb", "PCB"),
        ("design", "Design"),
        ("other", "Other"),
    ]

    quote_number = models.CharField(max_length=20, unique=True, editable=False)

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(max_length=100, blank=True)
    customer_company = models.CharField(max_length=200, blank=True)

    service = models.CharField(max_length=20, choices=SERVICE_CHOICES, default="other")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True)

    customer_notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    # Internal costing. The quoted price comes from the line items; these
    # record what the job costs us, so the margin can be derived rather than
    # entered twice and left to drift.
    materials_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    machining_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    additional_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    converted_order = models.ForeignKey(
        "Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_quotes",
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.quote_number:
            from datetime import datetime

            prefix = datetime.now().strftime("%Y%m")
            unique_part = str(uuid.uuid4().int)[:4]
            self.quote_number = f"Q-{prefix}-{unique_part}"
        super().save(*args, **kwargs)

    # --- Derived totals ---------------------------------------------------
    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    @property
    def cost_total(self):
        return self.materials_cost + self.machining_cost + self.additional_cost

    @property
    def margin_amount(self):
        return self.subtotal - self.cost_total

    @property
    def margin_percent(self):
        if not self.cost_total:
            return None
        return (self.margin_amount / self.cost_total) * 100

    def __str__(self):
        return f"{self.quote_number} | {self.customer_name} | {self.status}"


class QuoteItem(models.Model):
    """A line on a quote. Free-text rather than a product FK, because quotes
    are often for things that do not exist in the catalogue yet."""

    PROCESS_CHOICES = [
        ("3d_print", "3D Print"),
        ("cnc", "CNC"),
        ("pcb", "PCB"),
        ("purchase", "Purchase"),
        ("labour", "Labour"),
        ("other", "Other"),
    ]

    quote = models.ForeignKey(Quote, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    spec = models.CharField(max_length=200, blank=True)
    process = models.CharField(max_length=20, choices=PROCESS_CHOICES, default="other")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.name} x{self.quantity}"


class Printer(models.Model):
    """A physical printer on the shop floor."""

    STATUS_IDLE = "idle"
    STATUS_PREPARING = "preparing"
    STATUS_PRINTING = "printing"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_OFFLINE = "offline"
    STATUS_CHOICES = [
        (STATUS_IDLE, "Idle"),
        (STATUS_PREPARING, "Preparing"),
        (STATUS_PRINTING, "Printing"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_OFFLINE, "Offline"),
    ]

    name = models.CharField(max_length=100, unique=True)
    model_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_IDLE)
    notes = models.CharField(max_length=300, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Material(models.Model):
    """A filament spool type kept in stock."""

    TYPE_CHOICES = [
        ("PLA", "PLA"),
        ("PLA+", "PLA+"),
        ("PETG", "PETG"),
        ("TPU", "TPU"),
        ("ABS", "ABS"),
    ]

    name = models.CharField(max_length=100, unique=True)
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="PLA")
    color = models.CharField(max_length=40, blank=True)
    color_hex = models.CharField(max_length=7, blank=True)
    stock_grams = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_gram = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PrintJob(models.Model):
    """One print on the production board."""

    STATUS_QUEUED = "queued"
    STATUS_PRINTING = "printing"
    STATUS_POST = "post"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_PRINTING, "Printing"),
        (STATUS_POST, "Post-Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    POST_STAGE_CHOICES = [
        ("supports", "Removing supports"),
        ("cleaning", "Cleaning"),
        ("painting", "Painting"),
        ("assembly", "Assembly"),
    ]

    job_number = models.CharField(max_length=20, unique=True, editable=False)
    file_name = models.CharField(max_length=200)

    printer = models.ForeignKey(
        Printer, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs"
    )
    material = models.ForeignKey(
        Material, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs"
    )

    quantity = models.PositiveIntegerField(default=1)
    layer_height = models.DecimalField(max_digits=4, decimal_places=2, default=0.20)
    infill_percent = models.PositiveIntegerField(default=15)

    # Progress is derived from these two plus started_at. There is no printer
    # integration, so it is an estimate from the planned duration, not a
    # reading from the machine.
    estimated_minutes = models.PositiveIntegerField(default=0)
    filament_estimated_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    filament_used_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    post_stage = models.CharField(max_length=12, choices=POST_STAGE_CHOICES, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=200, blank=True)

    order = models.ForeignKey(
        "Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="print_jobs"
    )
    quote = models.ForeignKey(
        "Quote", null=True, blank=True, on_delete=models.SET_NULL, related_name="print_jobs"
    )
    note = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.job_number:
            self.job_number = f"P-{str(uuid.uuid4().int)[:4]}"
        super().save(*args, **kwargs)

    # --- Derived timing ---------------------------------------------------
    @property
    def elapsed_minutes(self):
        if not self.started_at:
            return 0
        from django.utils import timezone

        end = self.completed_at or timezone.now()
        return max(0, int((end - self.started_at).total_seconds() // 60))

    @property
    def progress_percent(self):
        """Estimated completion, 0-100.

        Derived from elapsed time against the planned duration. Capped at 99
        while still printing so a job that overruns never looks finished.
        """
        if self.status in (self.STATUS_COMPLETED, self.STATUS_POST):
            return 100
        if self.status == self.STATUS_FAILED:
            return 0
        if self.status != self.STATUS_PRINTING or not self.estimated_minutes:
            return 0
        pct = int((self.elapsed_minutes / self.estimated_minutes) * 100)
        return max(0, min(99, pct))

    @property
    def remaining_minutes(self):
        if self.status != self.STATUS_PRINTING or not self.estimated_minutes:
            return 0
        return max(0, self.estimated_minutes - self.elapsed_minutes)

    @property
    def estimated_finish(self):
        if not self.started_at or not self.estimated_minutes:
            return None
        from datetime import timedelta

        return self.started_at + timedelta(minutes=self.estimated_minutes)

    def __str__(self):
        return f"{self.job_number} | {self.file_name} | {self.status}"
