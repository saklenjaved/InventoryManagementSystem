from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import LoginActivity, UserProfile
from inventory.models import Category, Product, Purchase, Sale

from .serializers import (
    CategorySerializer,
    ProductSerialzer,
    UserProfileSerializer,
    PurchaseSerializer,
    SaleSerializer,
)
from .tasks import enqueue_signup_notification

User = get_user_model()

@api_view(['GET'])
def getRoutes(request):
    routes = [
        'GET api/',
        'POST api/register',
        'POST api/login/',
        'POST api/logout/',
        'POST api/token/refresh/',
        'GET api/userslist',

        'GET api/categories/',
        'POST api/create-category/',
        'PUT api/update-category/<str:category_id>/',               # with put update all data
        'DELETE api/delete-category/<str:category_id>/',
        
        'GET api/products/',
        'POST api/create-product/<str:category_id>/', 
        'PATCH api/update-product/<str:product_id>/',                # in put you update specific fields
        'DELETE api/delete-product/<str:product_id>/',

        'GET api/purchases/',
        'POST api/create-purchase/',

        'GET api/sales/',
        'POST api/create-sale/',
    ]
    return Response(routes) 

@api_view(['POST'])
# @authentication_classes([])
@permission_classes([AllowAny])
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
    
    
    if not username or not email or not password:
        return Response(
            {'detail': 'username, email, and password are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
        )
        UserProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            city=city,
            state=state,
        )
    except IntegrityError:
        return Response(
            {'detail': 'Username or email already registered.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    enqueue_signup_notification(email=user.email, username=user.username)

    return Response(
        {'detail': 'Registration successful'},
        status=status.HTTP_201_CREATED,
    )

@api_view(['POST'])
# @authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"detail": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TokenObtainPairSerializer(data={"username": username, "password": password})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(
            {'detail': 'User not found.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    request.session['accounts_user_id'] = user.pk
    LoginActivity.objects.create(user=user)
    return Response(
        {
            "message": "Login successful",
            "access": serializer.validated_data["access"],
            "refresh": serializer.validated_data["refresh"],
            "user": {"id": user.id, "username": user.username, "role": user.role},
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    request.session.pop('accounts_user_id', None)
    return Response(
        {
            "message": (
                "Logout successful. Clear JWT on the client; Django session cleared for HTML pages."
            ),
        },
        status=status.HTTP_200_OK,
    )

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getUsers(request):
    user = request.user
    
    if user.role != 'admin':
        return Response("Only Admin Shows This List")

    users = UserProfile.objects.all()
    serializer = UserProfileSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getCategories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createCategory(request):
    user = request.user
    
    if user.role != 'admin':
        return Response("Only Admin Create categories")
    
    name = request.data.get('name')
    category = Category.objects.create(name = name)
    
    return Response("Category Added")


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updateCategory(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid category id'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    if user.role != 'admin':
        return Response("Only Admin can update category")

    serializer = CategorySerializer(category, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteCategory(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid category id'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    if user.role != 'admin':
        return Response("Admin can delete categories")

    category.delete()
    return Response({'detail': 'Category deleted'}, status=status.HTTP_200_OK)

# Products

@api_view(['GET'])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerialzer(products, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createProduct(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid category id'}, status=status.HTTP_400_BAD_REQUEST)
    user = request.user
    
    if user.role != 'admin':
        return Response("Only Admin can Add New Products")
    
    serializer = ProductSerialzer(data={
        'name': request.data.get('name'),
        'description': request.data.get('description', ''),
        'price': request.data.get('price'),
        'quantity': request.data.get('quantity'),
        'category': category.id,

    })
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updateProduct(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid product id'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    if user.role != 'admin':
        return Response("Only admin can Update Product")

    serializer = ProductSerialzer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteProduct(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid product id'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    if user.role != 'admin':
        return Response("Only admin can delete Products")

    product.delete()
    return Response({'detail': 'Product deleted'}, status=status.HTTP_200_OK)


# Purchases

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def  getPurchase(request):
    user = request.user
    if user.role != 'admin':
        return Response("Only admin can view purchases")
    
    purchases = Purchase.objects.all()
    serializer = PurchaseSerializer(purchases, many=True)
    return Response(serializer.data)    


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createPurchase(request):
    user = request.user
    if user.role != 'admin':
        return Response("Only admin can create purchases")
    
    serializer = PurchaseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(buyer=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Sells

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getSales(request):
    user = request.user
    qs = Sale.objects.select_related('product', 'customer').order_by('-date', '-id')
    if user.role != 'admin':
        qs = qs.filter(customer=user)

    serializer = SaleSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createSale(request):
    """Shop-style buy: stock decreases; sale.customer = logged-in JWT user."""
    serializer = SaleSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)