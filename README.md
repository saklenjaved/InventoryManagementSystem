Inventory Management System
- This is inventory management system project built in using Django for manage stocks for admin, and buy products for user,

This Project supported two roles:
1. Admin - Manages products, categories, purchases and sells.
2. User - Browse products, add to cart and buy items

Models : 
1. User
2. UserProfile
3. Category
4. Product
5. Purchase
6. Sell


Features: 
Admin Feature
* add/update/delete categories
* add/update/delete products
* manage purchases
* manage sells
* Admin Dashboard shows:
    - Total Products
    - Total categories
    - Total Purchases
    - Total Sells
    - Total Stock

User Features
* View Available products
* Register and login
* Add products to cart
* update/delete cart items
* Buy products


Middleware in project : AccountsUserMiddleware
1. Takes user ID from session
2. Fetches user from database
3. Attaches user to request object
   with : request.accounts_user
4. Makes user available in all views & templates


Mixin : InventoryAdminRequiredMixin
1. Checks if user is logged in
2. Check if user role = admin
3. Write in Class based Views

Decorator : Function-Based Views
1. Creates Wrapper functions
2. Wrap function based views
3. Checks if user exists
4. Checks user role = admin


Inventory Logic:
 * Purchase -> Stock Increases
 * Item sells -> Stock Decreases
 * Cart -> Temparory saved items before buy
