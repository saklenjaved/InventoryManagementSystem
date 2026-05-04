from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from inventory.models import User, UserProfile, Category, Product, Purchase, Sell


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        
class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'    

class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        
class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class PurchaseSerializer(ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'
        
class SellSerializer(ModelSerializer):
    class Meta:
        model = Sell
        fields = '__all__'