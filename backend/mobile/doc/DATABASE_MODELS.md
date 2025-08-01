# Database Models for Mobile API

This document outlines the database models used by the mobile API and their relationships.

## Core Models

### User Model (`backend.models.User`)
```python
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(choices=[('CLIENT', 'Client'), ('ADMIN', 'Administrateur')])
    city = models.CharField(max_length=20, choices=CITIES)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='users/profiles/')
    is_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    trust_score = models.IntegerField(default=100)
    loyalty_points = models.IntegerField(default=0)
    loyalty_level = models.CharField(default='bronze')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `id`: Unique identifier
- `email`: Primary login field
- `phone`: Required for verification
- `user_type`: Determines permissions (CLIENT/ADMIN)
- `city`: Used for location-based features
- `is_verified` & `phone_verified`: Security status

### Product Model (`backend.models.Product`)
```python
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(choices=CONDITIONS)
    status = models.CharField(choices=STATUSES, default='ACTIVE')
    is_negotiable = models.BooleanField(default=True)
    city = models.CharField(max_length=20, choices=User.CITIES)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `id`: Unique identifier
- `title`, `description`: Product information
- `price`: Cost in FCFA
- `condition`: Product state (NEUF, EXCELLENT, etc.)
- `status`: Product availability (ACTIVE, PENDING, etc.)
- `city`: Location for filtering
- `seller`: User who listed the product

### Category Model (`backend.models.Category`)
```python
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `id`: Unique identifier
- `name`: Category name
- `slug`: URL-friendly identifier
- `icon`: Icon identifier for mobile UI
- `parent`: For subcategories
- `is_active`: Whether category is available

### Order Model (`backend.models.Order`)
```python
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order_number = models.CharField(max_length=20, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=STATUSES, default='PENDING')
    payment_method = models.CharField(choices=PAYMENT_METHODS)
    delivery_method = models.CharField(choices=DELIVERY_METHODS)
    
    # Visitor fields (for non-authenticated users)
    visitor_name = models.CharField(max_length=100, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `id`: Unique identifier
- `product`: The product being ordered
- `buyer`: Authenticated user (null for visitors)
- `visitor_*`: Fields for non-authenticated users
- `status`: Order progress (PENDING, PAID, DELIVERED, etc.)
- `total_amount`: Total cost including delivery

## Advanced Models

### Wallet Model (`backend.models_advanced.Wallet`)
```python
class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `balance`: Available funds
- `pending_balance`: Funds in processing
- `total_earned` & `total_spent`: Financial statistics
- `is_frozen`: Account status

### Transaction Model (`backend.models_advanced.Transaction`)
```python
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    status = models.CharField(choices=STATUSES, default='PENDING')
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Fields for Mobile:**
- `transaction_type`: CREDIT, DEBIT, COMMISSION, etc.
- `amount`: Transaction value
- `description`: Human-readable description
- `status`: Transaction state
- `reference`: External reference number

## Visitor Models

### VisitorCart Model (`backend.models_visitor.VisitorCart`)
```python
class VisitorCart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session_key = models.CharField(max_length=100, unique=True)
    
    # Visitor information
    visitor_name = models.CharField(max_length=100, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_phone = models.CharField(max_length=20, blank=True)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Delivery and payment preferences
    delivery_method = models.CharField(choices=DELIVERY_METHODS, default='PICKUP')
    payment_option = models.CharField(choices=PAYMENT_OPTIONS, default='WHATSAPP_PICKUP')
    delivery_address = models.TextField(blank=True)
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and tracking
    is_active = models.BooleanField(default=True)
    is_abandoned = models.BooleanField(default=False)
    abandoned_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `session_key`: Unique session identifier
- `visitor_*`: Customer information
- `delivery_method`: PICKUP or DELIVERY
- `payment_option`: Payment preference
- `is_active` & `is_abandoned`: Cart status

### VisitorCartItem Model (`backend.models_visitor.VisitorCartItem`)
```python
class VisitorCartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cart = models.ForeignKey(VisitorCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `cart`: Parent cart
- `product`: Product being added
- `quantity`: Number of items
- `unit_price`: Price at time of addition
- `notes` & `special_requests`: Additional information

## Supporting Models

### PickupPoint Model (`backend.models.PickupPoint`)
```python
class PickupPoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=20, choices=User.CITIES)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    opening_hours = models.JSONField(default=dict, blank=True)
    capacity = models.PositiveIntegerField(default=100)
    processing_time = models.PositiveIntegerField(default=24)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `name`: Location name
- `address`: Physical address
- `city`: City location
- `phone` & `email`: Contact information
- `is_active`: Availability status
- `opening_hours`: Operating hours (JSON)

### Favorite Model (`backend.models.Favorite`)
```python
class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Fields for Mobile:**
- `user`: User who favorited
- `product`: Favorited product
- `created_at`: When it was added

### Review Model (`backend.models.Review`)
```python
class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    product_quality = models.IntegerField(choices=RATING_CHOICES)
    seller_communication = models.IntegerField(choices=RATING_CHOICES)
    delivery_speed = models.IntegerField(choices=RATING_CHOICES)
    packaging = models.IntegerField(choices=RATING_CHOICES)
    overall_rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    images = models.JSONField(default=list, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields for Mobile:**
- `order`: Associated order
- `reviewer`: User giving review
- `*_rating`: Individual rating categories
- `overall_rating`: Overall score
- `comment`: Review text
- `images`: Review photos (JSON array)

## Model Relationships

### User Relationships
- **Products**: `user.products_sold` - Products listed by user
- **Orders**: `user.orders_bought` - Orders purchased by user
- **Favorites**: `user.favorites` - User's favorite products
- **Reviews**: `user.reviews_given` - Reviews written by user
- **Wallet**: `user.wallet` - User's wallet (OneToOne)

### Product Relationships
- **Category**: `product.category` - Product category
- **Seller**: `product.seller` - User who listed product
- **Images**: `product.images` - Product images
- **Orders**: `product.orders` - Orders for this product
- **Favorites**: `product.favorited_by` - Users who favorited
- **Reviews**: `product.reviews` - Product reviews

### Order Relationships
- **Product**: `order.product` - Product being ordered
- **Buyer**: `order.buyer` - User purchasing (null for visitors)
- **Seller**: `order.seller` - User selling the product
- **PickupPoint**: `order.pickup_point` - Pickup location
- **Review**: `order.review` - Review for this order (OneToOne)

### Cart Relationships
- **Items**: `cart.items` - Items in cart
- **PickupPoint**: `cart.pickup_point` - Selected pickup point

## Database Constraints

### Unique Constraints
- `User.email` - Email must be unique
- `User.phone` - Phone must be unique
- `Product.slug` - Product slug must be unique
- `Category.slug` - Category slug must be unique
- `Order.order_number` - Order number must be unique
- `VisitorCart.session_key` - Session key must be unique
- `Favorite.user + Favorite.product` - User can favorite product once

### Foreign Key Constraints
- All foreign keys have `on_delete` rules defined
- `CASCADE` for strong relationships (delete product → delete orders)
- `SET_NULL` for optional relationships (delete pickup point → set order pickup to null)

## Indexes

### Performance Indexes
- `User.email` - Fast login lookups
- `User.phone` - Fast phone verification
- `Product.status + Product.created_at` - Active product listings
- `Product.city + Product.category` - Location/category filtering
- `Order.buyer + Order.created_at` - User order history
- `Order.seller + Order.created_at` - Seller order history
- `VisitorCart.session_key` - Fast cart lookups
- `Transaction.wallet + Transaction.created_at` - Transaction history

## Mobile API Considerations

### UUID Primary Keys
All models use UUID primary keys for:
- Security (non-sequential IDs)
- Mobile app compatibility
- API consistency

### JSON Fields
Several models use JSON fields for flexible data:
- `PickupPoint.opening_hours` - Operating hours
- `Review.images` - Review photos
- `VisitorCart.behavior_data` - Analytics data

### Nullable Fields
Visitor-related fields are nullable to support:
- Anonymous shopping
- Partial user registration
- Optional information

### Timestamps
All models include:
- `created_at` - Record creation time
- `updated_at` - Last modification time

This ensures proper tracking and mobile app synchronization. 