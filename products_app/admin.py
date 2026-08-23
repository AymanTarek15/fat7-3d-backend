from django.contrib import admin
from products_app.models import Category,ProductList,Review,Colour,Order,OrderItem,OrderStatus,SeasonChange,ProductImage,ProductColour,ContactMessage
from django.utils.html import format_html

# Register your models here.

admin.site.register(Category)
admin.site.register(ProductList)
admin.site.register(Review)
admin.site.register(Colour)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(OrderStatus)
admin.site.register(SeasonChange)
admin.site.register(ProductImage)
admin.site.register(ProductColour)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "handled", "created")
    list_filter = ("handled", "created")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created")
    list_editable = ("handled",)





