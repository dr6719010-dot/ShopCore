markdown# ShopCore - E-Commerce Backend API

A production-style e-commerce backend API built with FastAPI, PostgreSQL, and Redis.

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Primary database (hosted on Neon)
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Redis** (Upstash) - Token blacklisting and caching
- **JWT** - Authentication
- **bcrypt** - Password hashing

## Features

### Completed
- User registration and login with JWT authentication
- Role-based access control (customer, seller, admin)
- Redis token blacklisting on logout
- Product management (CRUD) for sellers
- Category management for admins
- Stock management for sellers
- Product filtering by category

### In Progress
- Order placement with stock management
- Cart (Redis-based)
- Payment gateway integration (Razorpay)
- Refresh tokens
- Redis caching for product listings
- Docker containerization

## Project Structure
app/

├── main.py

├── database.py

├── dependencies.py

├── config.py

├── cache.py

├── auth/

│   ├── jwt.py

│   ├── router.py

│   ├── schemas.py

│   └── service.py

├── users/

│   ├── models.py

│   ├── router.py

│   ├── schemas.py

│   └── service.py

├── products/

│   ├── models.py

│   ├── router.py

│   ├── schemas.py

│   └── service.py

├── orders/

│   ├── models.py

│   ├── router.py

│   ├── schemas.py

│   └── service.py

├── cart/

│   └── router.py

└── payments/

├── router.py

└── service.py

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL database
- Redis instance

### Installation

1. Clone the repository
```bash
git clone https://github.com/dr6719010-dot/ShopCore
cd ShopCore
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create `.env` file in the project root
DATABASE_URL=postgresql://username:password@host:port/dbname

UPSTASH_REDIS_URL=https://your-upstash-url

UPSTASH_REDIS_TOKEN=your-upstash-token

SECRET_KEY=your-secret-key

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60

RAZORPAY_KEY_ID=your-razorpay-key

RAZORPAY_KEY_SECRET=your-razorpay-secret

4. Run database migrations
```bash
alembic upgrade head
```

5. Start the server
```bash
uvicorn app.main:app --reload
```

6. Visit API docs at `http://localhost:8000/docs`

## API Endpoints

### Auth
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | /auth/register | Public | Register a new user |
| POST | /auth/login | Public | Login and get JWT token |
| POST | /auth/logout | Authenticated | Logout and blacklist token |

### Products
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | /products/ | Public | Get all products |
| GET | /products/{id} | Public | Get a single product |
| POST | /products/ | Seller | Create a product |
| PUT | /products/{id} | Seller | Update a product |
| DELETE | /products/{id} | Seller | Delete a product |
| POST | /products/{id}/stock | Seller | Update stock |
| GET | /products/category/{id} | Public | Filter by category |

### Categories
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | /products/categories | Public | Get all categories |
| POST | /products/categories | Admin | Create a category |

## Environment Variables

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| UPSTASH_REDIS_URL | Upstash Redis URL |
| UPSTASH_REDIS_TOKEN | Upstash Redis token |
| SECRET_KEY | JWT signing secret |
| ALGORITHM | JWT algorithm (HS256) |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry in minutes |
| RAZORPAY_KEY_ID | Razorpay API key |
| RAZORPAY_KEY_SECRET | Razorpay secret key |

## License

MIT


---project under progress---