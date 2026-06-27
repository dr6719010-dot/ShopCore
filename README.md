# ShopCore — Production-Style E-Commerce Backend API

> A fully deployed, production-style e-commerce backend built with FastAPI, PostgreSQL, and Redis.

**Live API:** https://shopcore-80ck.onrender.com  
**Interactive Docs:** https://shopcore-80ck.onrender.com/docs

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | FastAPI | Async-ready, automatic OpenAPI docs, Pydantic validation |
| Database | PostgreSQL (Neon) | ACID transactions, concurrent writes, enum support |
| ORM | SQLAlchemy | Type-safe queries, relationship management, migration support |
| Migrations | Alembic | Version-controlled schema changes, never drop-and-recreate |
| Caching | Redis (Upstash) | Sub-millisecond reads, TTL support, cart storage |
| Auth | JWT (python-jose) | Stateless authentication, role embedded in token |
| Password Hashing | bcrypt | Industry standard, automatic salt, slow by design |
| Payment Gateway | Razorpay | Webhook support, INR native, widely used in India |
| Deployment | Render | Zero-config deployment, auto-deploys from GitHub |

---

## Architecture

```
Client
  │
  ▼
FastAPI Application
  │
  ├── Auth Layer (JWT + RBAC)
  │     ├── Access Token (15 min)
  │     ├── Refresh Token (7 days)
  │     └── Redis Blacklist (logout)
  │
  ├── API Routes
  │     ├── /auth      → register, login, logout, refresh
  │     ├── /products  → CRUD + category filtering
  │     ├── /orders    → place, view, cancel, status
  │     ├── /cart      → Redis-based, no DB
  │     └── /payments  → Razorpay integration + webhooks
  │
  ├── Service Layer (business logic)
  │
  ├── PostgreSQL (Neon)
  │     ├── users, products, categories
  │     ├── orders, orderitems, stock
  │     ├── payments, productcategories
  │     └── Numeric columns for money (no float precision issues)
  │
  └── Redis (Upstash)
        ├── Cart storage (TTL: 7 days)
        ├── Token blacklist (TTL: token expiry)
        └── Product cache (TTL: 10 min)
```

---

## Features

### Authentication
- User registration with role selection (customer / seller)
- Admin role is never self-assignable — granted only by existing admins
- JWT access tokens (15 min) + refresh tokens (7 days)
- bcrypt password hashing
- Redis token blacklisting on logout — tokens are truly invalidated
- Role-based access control on every protected route

### Products
- Sellers create, update, and delete their own products
- Products linked to multiple categories via junction table
- Stock managed separately per product
- Category management by admins only
- Redis caching on all GET endpoints (10 min TTL)
- Cache invalidated automatically on any write operation

### Orders
- Customers place orders with multiple items in one request
- Pessimistic locking on stock rows — prevents overselling under concurrent load
- Items sorted by product_id before locking — prevents deadlocks
- Atomic transactions — order + stock decrement succeed or fail together
- Order cancellation restores stock automatically
- Sellers update shipping status (shipped / delivered)
- Price locked at purchase time — price changes don't affect past orders

### Cart
- Stored entirely in Redis — no database load
- Persists across sessions using user email as key
- TTL resets on every interaction — active carts never expire
- Add, update, remove items, or clear cart

### Payments
> **Note:** Payment integration is implemented with full Razorpay SDK integration and webhook handling. However, live payment processing requires a verified Razorpay merchant account (PAN required for Indian merchants). Currently running in mock mode — all payment logic, signature verification, and webhook handling is production-ready and will work immediately upon adding valid Razorpay credentials.
- Razorpay order creation — returns payment intent to frontend
- Webhook handler verifies Razorpay signature before processing
- Handles both `order.paid` and `payment.captured` event types
- Orphaned payment detection with error logging
- Payment status and order status updated atomically

---

## Architecture Decisions

### Why PostgreSQL over SQLite?
SQLite doesn't support concurrent writes. In e-commerce, two users can attempt to buy the last item simultaneously. PostgreSQL handles this with row-level locking (`SELECT FOR UPDATE`), which SQLite cannot do.

### Why Redis for Cart?
Carts are temporary. Storing them in PostgreSQL wastes database resources and pollutes order history with abandoned carts. Redis gives fast reads, automatic expiry, and zero schema complexity.

### Why Pessimistic Locking for Stock?
Optimistic locking requires retry logic and can still result in failed transactions under high concurrency. For stock — a hard business resource — we lock the row before reading it. The performance cost is acceptable; overselling is not.

### Why Separate `price_at_purchase` on OrderItem?
Product prices change. Storing the price at the moment of purchase protects historical order data from being corrupted by future price updates.

### Why `Numeric` instead of `Float` for money?
`0.1 + 0.2 = 0.30000000000000004` in floating point. For financial calculations this causes real errors. `Numeric(precision=10, scale=2)` gives exact decimal arithmetic.

### Why Alembic instead of `create_all()`?
`create_all()` cannot modify existing tables. Alembic generates versioned migration files that can be applied, rolled back, and tracked in git — essential for production databases with real data.

### Why short-lived access tokens with refresh tokens?
A 60-minute access token that cannot be revoked is a security risk. With 15-minute access tokens and Redis blacklisting on logout, the maximum exposure window after logout is 15 minutes. Refresh tokens allow seamless re-authentication without forcing users to log in again.

### Why sort items by product_id before locking?
Without consistent lock ordering, two concurrent orders can deadlock — Request A locks product 1 and waits for product 2, while Request B locks product 2 and waits for product 1. Sorting ensures all requests acquire locks in the same order, eliminating this scenario.

---

## Known Bottlenecks

### Single Database Connection Pool
Currently using SQLAlchemy's default connection pool. Under high traffic this becomes a bottleneck. Production fix: configure `pool_size` and `max_overflow` on the engine, or use PgBouncer as a connection pooler.

### Redis Cache Invalidation is Coarse
`invalidate_product_cache()` deletes all product cache keys on any write. Under high write volume this causes cache stampedes — many requests hit the database simultaneously after a cache clear. Production fix: use cache versioning or per-product invalidation with a distributed lock.

### Webhook Endpoint Has No Rate Limiting
The `/payments/webhook` endpoint is public and unauthenticated (by design — Razorpay calls it). Without rate limiting, it's vulnerable to DoS attacks. Production fix: add IP whitelisting for Razorpay's IP ranges and rate limiting middleware.

### No Background Task Queue
Order confirmation emails, stock alerts, and analytics events are not implemented. In production these should run in a background task queue (Celery + Redis) to avoid blocking the request cycle.

### Render Free Tier Spins Down
The deployed instance on Render's free tier spins down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds. Production fix: upgrade to a paid instance or use a cron job to ping the server every 10 minutes.

### No Pagination on List Endpoints
`GET /products` and `GET /orders` return all records. With thousands of products this becomes slow and expensive. Production fix: add `limit` and `offset` query parameters to all list endpoints.

---

## Database Schema

```
users
  id, email, password_hash, role (enum), is_active, created_at

products
  id, seller_id (FK→users), name, description, price (Numeric), created_at

categories
  id, name, description

product_categories (junction)
  product_id (FK→products), category_id (FK→categories)

stock
  id, product_id (FK→products), quantity

orders
  id, user_id (FK→users), status (enum), total_amount (Numeric), cancel_reason, created_at

order_items
  id, order_id (FK→orders), product_id (FK→products), quantity, price_at_purchase (Numeric)

payments
  id, order_id (FK→orders), amount (Numeric), status (enum), payment_gateway_id, created_at
```

---

## API Endpoints

### Auth
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | /auth/register | Public | Register as customer or seller |
| POST | /auth/login | Public | Login, receive access + refresh token |
| POST | /auth/logout | Authenticated | Blacklist token in Redis |
| POST | /auth/refresh | Authenticated | Get new access token |

### Products
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | /products/ | Public | All products (cached) |
| GET | /products/{id} | Public | Single product (cached) |
| POST | /products/ | Seller | Create product |
| PUT | /products/{id} | Seller | Update own product |
| DELETE | /products/{id} | Seller | Delete own product |
| POST | /products/{id}/stock | Seller | Update stock |
| GET | /products/category/{id} | Public | Filter by category (cached) |
| GET | /products/categories | Public | All categories (cached) |
| POST | /products/categories | Admin | Create category |

### Orders
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | /orders | Customer | Place order with multiple items |
| GET | /orders | Customer | View own orders |
| GET | /orders/{id} | Customer | View single order |
| PATCH | /orders/{id}/cancel | Customer | Cancel with reason, restores stock |
| GET | /orders/seller | Seller | View orders containing their products |
| GET | /orders/admin | Admin | View all orders |
| PUT | /orders/{id}/status | Seller | Update to shipped/delivered |

### Cart
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | /cart | Authenticated | View cart |
| POST | /cart | Authenticated | Add item |
| PUT | /cart/{product_id} | Authenticated | Update quantity |
| DELETE | /cart/{product_id} | Authenticated | Remove item |
| DELETE | /cart | Authenticated | Clear cart |

### Payments
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | /payments/{order_id} | Customer | Initiate payment |
| POST | /payments/webhook | Public | Razorpay webhook handler |

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database (or Neon free tier)
- Redis instance (or Upstash free tier)

### Installation

```bash
git clone https://github.com/dr6719010-dot/ShopCore
cd ShopCore
pip install -r requirements.txt
```

Create `.env` in project root:
```
DATABASE_URL=postgresql://username:password@host:port/dbname
UPSTASH_REDIS_URL=https://your-upstash-url
UPSTASH_REDIS_TOKEN=your-upstash-token
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret
```

Run migrations:
```bash
alembic upgrade head
```

Start server:
```bash
uvicorn app.main:app --reload
```

Visit: `http://localhost:8000/docs`

---

## Project Structure

```
app/
├── main.py           # FastAPI app, router registration
├── database.py       # SQLAlchemy engine and session
├── dependencies.py   # get_db, get_current_user, require_role
├── config.py         # Pydantic settings from .env
├── cache.py          # Redis client, blacklist functions
│
├── auth/             # JWT, login, register, logout, refresh
├── users/            # User model
├── products/         # Products, categories, stock
├── orders/           # Order placement, cancellation, status
├── cart/             # Redis cart operations
└── payments/         # Razorpay integration, webhooks
```

---

## License

MIT