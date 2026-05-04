from django.db import transaction

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from accounts.models import UserProfile
from inventory.models import Category, Product, Purchase, Sale


class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerialzer(ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class PurchaseSerializer(serializers.ModelSerializer):
    buyer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ('date',)

    def get_buyer(self, obj):
        return obj.buyer.username

    def create(self, validated_data):
        buyer = validated_data.pop('buyer')
        with transaction.atomic():
            product = validated_data['product']
            qty = validated_data['quantity']
            locked = Product.objects.select_for_update().get(pk=product.pk)
            locked.quantity += qty
            locked.save(update_fields=['quantity'])
            return Purchase.objects.create(buyer=buyer, **validated_data)

class SaleSerializer(serializers.ModelSerializer):
    """Read: customer = buyer user id; customer_username for display."""

    customer_username = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Sale
        fields = (
            'id',
            'product',
            'quantity',
            'price',
            'customer',
            'customer_username',
            'date',
        )
        read_only_fields = ('id', 'price', 'customer', 'customer_username', 'date')

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError('Authentication required.')

        product = validated_data['product']
        qty = validated_data['quantity']
        with transaction.atomic():
            locked = Product.objects.select_for_update().get(pk=product.pk)
            if locked.quantity < qty:
                raise serializers.ValidationError(
                    {'quantity': f'Not enough stock. Available: {locked.quantity}.'}
                )
            locked.quantity -= qty
            locked.save(update_fields=['quantity'])
            return Sale.objects.create(
                product=locked,
                quantity=qty,
                price=locked.price,
                customer=user,
            )