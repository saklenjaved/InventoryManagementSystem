from inventory.models import User, UserProfile, Category, Product, Purchase, Sell
from .serializers import UserSerializer, UserProfileSerializer, CategorySerializer, ProductSerializer, PurchaseSerializer, SellSerializer
from rest_framework.decorators import api_view
from inventory.api import serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

@api_view(['GET'])
def getRoutes(request):
    routes = [
        'GET api/',
        'POST api/register/',
        'POST api/login/',
        'POST api/logout/',
        'POST api/getusers/',
        
        'GET api/categories/',
        'POST api/create-category/',
        'PATCH api/update-category/<str:category_id>',
        'DELETE api/delete-category/<str:category_id>',
        
        'POST api/create-product/',
        'GET api/products/',
        'PATCH api/update-product/<str:product_id>',
        'DELETE api/delete-product/<str:product_id>',
        
    ]
    return Response(routes)

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    role = request.data.get('role', 'user')
    
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    phone = request.data.get('phone', '')
    address = request.data.get('address', '')
    city = request.data.get('city', '')
    state = request.data.get('state', '')
    
    if not username or not email:
        return Response("All fields are Required")

    user = User.objects.create_user(
        username = username,
        email = email,
        password=password,
        role=role,      
    )
    UserProfile.objects.create(
        user = user,
        first_name = first_name,
        last_name = last_name,
        phone = phone,
        address = address,
        city = city,
        state = state,   
    )
    return Response("Registration Successfull")


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = User.objects.get(username=username)
    
    if not check_password(password, user.password):
        return Response("Invalid Password")
    
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh)
        })
    

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response("Logged Out")
    except Exception:
        return Response("Error")   
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUsers(request):
    user = request.user
    
    if user.role != 'admin':
        return Response("Only Admin Allowed")
    
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    
    return Response(serializer.data)
    

@api_view(['GET'])
def getCategories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createCategory(request):
    user = request.user
    
    if user.role != 'admin':
        return Response("Only Admin can create category.")
    
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def updateCategory(request, category_id):
    category = Category.objects.get(id=category_id)
    user = request.user
    
    if user.role != 'admin':
        return Response("Admin Required")
    
    serializer = CategorySerializer(category, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteCategory(request, category_id):
    category = Category.objects.get(id=category_id)
    
    user = request.user
    
    if user.role != 'admin':
        return Response("Admin Required")
    
    category.delete()
    return Response("Category Deleted")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProducts(request):
    
    # user = request.user
    
    if request.user.role != 'admin':
        return Response("Admin Only")
    
    serializer = ProductSerializer(data=request.data)
        # data = {
        #     'name': request.data.get('name'),
        #     'category': category.id,
        #     'price': request.data.get('price'),
        #     'stock': request.data.get('stock'),            
        # }
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def updateProduct(request, product_id):
    product = Product.objects.get(id=product_id)
    
    user = request.user
    
    if user.role != 'admin':
        return Response("Admin Only")
    
    serializer = ProductSerializer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteProduct(request, product_id):
    product = Product.objects.get(id=product_id)
    
    user = request.user
    
    if user.role != 'admin':
        return Response("only admin can delete product")
    
    product.delete()
    return Response("Product Deleted")

# @api_view(['POST'])
