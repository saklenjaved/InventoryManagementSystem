from django.urls import path
from . import views
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('', views.getRoutes),
    path('register/', views.register),
    
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),   
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    
    # path('login/', views.login),
    path('logout/', views.logout),
    path('getusers/', views.getUsers),
    
    path('categories/', views.getCategories),
    path('create-category/', views.createCategory),
    path('update-category/<str:category_id>/', views.updateCategory),
    path('delete-category/<str:category_id>/', views.deleteCategory),
    
    path('create-product/', views.createProducts),
    path('products/', views.getProducts),
    path('update-product/<str:product_id>/', views.updateProduct),
    path('delete-product/<str:product_id>/', views.deleteProduct),
    
]
