# 🛒 Supermarket Backend API

Flask REST API for the Supermarket e-commerce application.

## 🐳 Docker Hub

**https://hub.docker.com/r/dotcoms/supermarket-backend**

```bash
docker pull dotcoms/supermarket-backend:latest
docker run -p 3000:3000 dotcoms/supermarket-backend:latest
```

## 🚀 Quick Start (Local)

```bash
cd backend-py
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1 
pip install -r requirements.txt
python seed_database.py   # Seed database (first time)
python -m src.main
```

Server runs at: http://localhost:3000

## 🔗 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login user |
| GET | `/api/auth/me` | Get current user |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | Get all products (paginated) |
| GET | `/api/products/:id` | Get product by ID |
| GET | `/api/products/stats` | Inventory aggregates for the admin dashboard (admin/manager) |
| POST | `/api/products` | Create product (admin/manager) |
| PUT | `/api/products/:id` | Update product (admin/manager) |
| DELETE | `/api/products/:id` | Delete product (admin) |

`GET /api/products/stats` returns `totalProducts`, `lowStockCount`,
`outOfStockCount`, `inventoryValue`, `lowStockThreshold` and `lowStockProducts`
(the 5 lowest-stock rows, each `{ id, name, stock, price }` — no `image`: the
dashboard panel has no thumbnail slot). All of it is computed in SQL over the
whole catalogue; clients must not re-derive it from a paginated page.

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | Get all categories (flat) |
| GET | `/api/categories/tree` | Get the nested category tree |
| GET | `/api/categories/:slug` | Get one category by slug, with breadcrumbs |
| GET | `/api/categories/:slug/products` | Get a category's products |
| POST | `/api/categories` | Create category (admin/manager) |
| GET | `/api/categories/:id` | Get category by numeric ID (admin/manager) |
| PUT | `/api/categories/:id` | Update category (admin/manager) |
| DELETE | `/api/categories/:id` | Delete category (admin) |

Note the numeric-ID rules win over `/:slug`, so `/api/categories/:slug` only
resolves for non-numeric slugs (all seeded slugs are non-numeric).

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orders` | **All** orders for admin/manager; returns `[]` for a customer |
| GET | `/api/orders/privet` | The logged-in user's own orders (see note) |
| GET | `/api/orders/:id` | Get one order (owner, or any admin/manager) |
| POST | `/api/orders` | Create order (checkout) |
| PUT | `/api/orders/:id` | Update status (admin/manager) |
| DELETE | `/api/orders/:id` | Delete order (admin) |

`/orders/privet` is a typo for "private" that shipped as the real route name.
It is what the customer-facing "My Orders" screen calls, so it is documented
as-is; renaming it would break the frontend.

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile` | Get the logged-in user's own profile |
| GET | `/api/users` | Get all users (admin, each with `ordersCount` and `totalSpent`) |
| PUT | `/api/users/:id/role` | Update role (admin) |

There is no `DELETE /api/users/:id` — user deletion is not implemented.

## 🔐 Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@test.com | Test123! |
| Manager | manager@test.com | Test123! |
| Customer | customer@test.com | Test123! |

## 🛠️ Tech Stack

- Python 3.11
- Flask
- SQLAlchemy (SQLite)
- JWT Authentication
- Flask-CORS

## 📁 Project Structure

```
backend-py/
├── src/
│   ├── config/        # Database config
│   ├── middleware/    # Auth, errors
│   ├── models/        # Database models
│   ├── routes/        # API routes (HTTP shaping)
│   ├── services/      # Business logic
│   ├── utils/         # Helpers
│   └── main.py        # Entry point
├── public/uploads/    # Product images
├── requirements.txt
└── seed_database.py
```

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 3000 |
| JWT_SECRET | JWT key | required |
| DB_STORAGE | Database path | ./database.sqlite |