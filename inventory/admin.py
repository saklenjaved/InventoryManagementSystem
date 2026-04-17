from django.contrib import admin
from .models import Category, Product, Purchase, Sale

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(Sale)
