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
source venv/bin/activate  # Windows: venv\Scripts\activate
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
| GET | `/api/products` | Get all products |
| GET | `/api/products/:id` | Get product by ID |
| POST | `/api/products` | Create product |
| PUT | `/api/products/:id` | Update product |
| DELETE | `/api/products/:id` | Delete product |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | Get all categories |
| POST | `/api/categories` | Create category |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orders` | Get user orders |
| POST | `/api/orders` | Create order |
| PUT | `/api/orders/:id/status` | Update status |

### Users (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | Get all users |
| PUT | `/api/users/:id/role` | Update role |
| DELETE | `/api/users/:id` | Delete user |

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
│   ├── controllers/   # Request handlers
│   ├── middleware/    # Auth, errors
│   ├── models/        # Database models
│   ├── routes/        # API routes
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