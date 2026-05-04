from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
    path('', views.getRoutes),
    path('register/', views.register),
    path('login/', views.login),
    path('logout/', views.logout),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('userslist/', views.getUsers),
    
    path('categories/', views.getCategories),
    path('create-category/', views.createCategory),
    path('update-category/<str:category_id>/', views.updateCategory),
    path('delete-category/<str:category_id>/', views.deleteCategory),
    
    path('products/', views.getProducts),
    path('create-product/<str:category_id>/', views.createProduct),
    path('update-product/<str:product_id>/', views.updateProduct),
    path('delete-product/<str:product_id>/', views.deleteProduct),
    
    path('purchases/', views.getPurchase),
    path('create-purchase/', views.createPurchase),

    path('sales/', views.getSales),
    path('create-sale/', views.createSale),
]
