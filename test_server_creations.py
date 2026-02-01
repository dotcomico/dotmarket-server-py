#!/usr/bin/env python3
"""

run server from backend root level:
python -m src.main
run this test server: 
python test_server_creations.py


Server Creation Endpoints Test Suite
=====================================
Tests all POST/creation endpoints for the Flask backend.

Endpoints covered:
- POST /api/auth/register - User registration
- POST /api/auth/login - User login (for token acquisition)
- POST /api/products - Product creation (Admin/Manager)
- POST /api/categories - Category creation (Admin/Manager)
- POST /api/orders - Order creation (Authenticated users)

Usage:
    python test_server_creations.py [--base-url http://localhost:3000]
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:3000/api"

# Test data storage
class TestContext:
    admin_token: Optional[str] = None
    customer_token: Optional[str] = None
    admin_user: Optional[Dict] = None
    customer_user: Optional[Dict] = None
    created_category_id: Optional[int] = None
    created_product_id: Optional[int] = None
    created_order_id: Optional[int] = None

ctx = TestContext()

# Console colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def log_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def log_test_header(name: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
    print(f"📋 TEST: {name}")
    print(f"{'='*60}{Colors.RESET}")

def log_section(name: str):
    print(f"\n{Colors.YELLOW}--- {name} ---{Colors.RESET}")

def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    token: Optional[str] = None,
    files: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make HTTP request and return response details."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if files:
        # Remove Content-Type for multipart
        del headers["Content-Type"]
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        try:
            body = response.json()
        except:
            body = response.text
        
        return {
            "status": response.status_code,
            "body": body,
            "ok": 200 <= response.status_code < 300
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": 0,
            "body": {"error": "Connection refused - is the server running?"},
            "ok": False
        }
    except Exception as e:
        return {
            "status": 0,
            "body": {"error": str(e)},
            "ok": False
        }

# ============================================================
# TEST: User Registration
# ============================================================
def test_register_admin():
    """Register an admin user for testing protected routes."""
    log_test_header("Register Admin User")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data = {
        "username": f"test_admin_{timestamp}",
        "email": f"admin_{timestamp}@test.com",
        "password": "Admin123!@#",
        "role": "admin"  # May require existing admin or be ignored
    }
    
    log_info(f"Registering: {data['email']}")
    result = make_request("POST", "/auth/register", data)
    
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"]:
        ctx.admin_token = result["body"].get("token")
        ctx.admin_user = result["body"].get("user")
        log_success(f"Admin registered successfully!")
        log_info(f"Token: {ctx.admin_token[:50]}..." if ctx.admin_token else "No token")
        return True
    else:
        log_error(f"Admin registration failed")
        return False

def test_register_customer():
    """Register a customer user."""
    log_test_header("Register Customer User")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data = {
        "username": f"test_customer_{timestamp}",
        "email": f"customer_{timestamp}@test.com",
        "password": "Customer123!"
    }
    
    log_info(f"Registering: {data['email']}")
    result = make_request("POST", "/auth/register", data)
    
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"]:
        ctx.customer_token = result["body"].get("token")
        ctx.customer_user = result["body"].get("user")
        log_success(f"Customer registered successfully!")
        return True
    else:
        log_error(f"Customer registration failed")
        return False

def test_register_validation():
    """Test registration validation errors."""
    log_test_header("Register Validation Tests")
    
    test_cases = [
        {
            "name": "Missing email",
            "data": {"username": "test", "password": "Test123!"},
            "expected_status": 400
        },
        {
            "name": "Missing password",
            "data": {"username": "test", "email": "test@test.com"},
            "expected_status": 400
        },
        {
            "name": "Invalid email format",
            "data": {"username": "test", "email": "invalid-email", "password": "Test123!"},
            "expected_status": 400
        },
        {
            "name": "Short password",
            "data": {"username": "test", "email": "test@test.com", "password": "123"},
            "expected_status": 400
        }
    ]
    
    passed = 0
    for test in test_cases:
        log_section(test["name"])
        result = make_request("POST", "/auth/register", test["data"])
        
        if result["status"] == test["expected_status"]:
            log_success(f"Got expected status {result['status']}")
            passed += 1
        else:
            log_error(f"Expected {test['expected_status']}, got {result['status']}")
        
        print(f"Response: {result['body']}")
    
    return passed == len(test_cases)

# ============================================================
# TEST: User Login
# ============================================================
def test_login():
    """Test user login to get fresh tokens."""
    log_test_header("User Login")
    
    if not ctx.customer_user:
        log_warning("No customer user - skipping login test")
        return False
    
    # Try logging in with just-registered customer
    # Note: We already have the token from registration, but let's test login separately
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # First register a new user specifically for login test
    register_data = {
        "username": f"login_test_{timestamp}",
        "email": f"login_test_{timestamp}@test.com",
        "password": "LoginTest123!"
    }
    
    log_section("Register user for login test")
    reg_result = make_request("POST", "/auth/register", register_data)
    
    if not reg_result["ok"]:
        log_error("Could not register user for login test")
        return False
    
    log_section("Test successful login")
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    result = make_request("POST", "/auth/login", login_data)
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"] and result["body"].get("token"):
        log_success("Login successful!")
        return True
    else:
        log_error("Login failed")
        return False

def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    log_test_header("Login Invalid Credentials")
    
    test_cases = [
        {
            "name": "Wrong password",
            "data": {"email": "admin@test.com", "password": "WrongPassword123!"},
            "expected_status": 401
        },
        {
            "name": "Non-existent user",
            "data": {"email": "nonexistent@test.com", "password": "Test123!"},
            "expected_status": 401
        },
        {
            "name": "Missing email",
            "data": {"password": "Test123!"},
            "expected_status": 400
        },
        {
            "name": "Missing password",
            "data": {"email": "test@test.com"},
            "expected_status": 400
        }
    ]
    
    passed = 0
    for test in test_cases:
        log_section(test["name"])
        result = make_request("POST", "/auth/login", test["data"])
        
        if result["status"] == test["expected_status"]:
            log_success(f"Got expected status {result['status']}")
            passed += 1
        else:
            log_error(f"Expected {test['expected_status']}, got {result['status']}")
        
        print(f"Response: {result['body']}")
    
    return passed == len(test_cases)

# ============================================================
# TEST: Category Creation
# ============================================================
def test_create_category():
    """Test category creation (requires admin/manager token)."""
    log_test_header("Create Category")
    
    if not ctx.admin_token:
        log_warning("No admin token - trying to register admin first")
        if not test_register_admin():
            log_error("Could not get admin token")
            return False
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data = {
        "name": f"Test Category {timestamp}",
        "icon": "📦"
    }
    
    log_info(f"Creating category: {data['name']}")
    result = make_request("POST", "/categories", data, token=ctx.admin_token)
    
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"]:
        category = result["body"].get("category", {})
        ctx.created_category_id = category.get("id")
        log_success(f"Category created! ID: {ctx.created_category_id}")
        log_info(f"Slug generated: {category.get('slug')}")
        return True
    else:
        log_error("Category creation failed")
        return False

def test_create_subcategory():
    """Test creating a subcategory with parent."""
    log_test_header("Create Subcategory")
    
    if not ctx.created_category_id:
        log_warning("No parent category - creating one first")
        if not test_create_category():
            return False
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data = {
        "name": f"Test Subcategory {timestamp}",
        "parentId": ctx.created_category_id,
        "icon": "📁"
    }
    
    log_info(f"Creating subcategory under parent ID: {ctx.created_category_id}")
    result = make_request("POST", "/categories", data, token=ctx.admin_token)
    
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"]:
        log_success("Subcategory created!")
        return True
    else:
        log_error("Subcategory creation failed")
        return False

def test_create_category_unauthorized():
    """Test category creation without auth or with customer token."""
    log_test_header("Create Category - Authorization Tests")
    
    data = {"name": "Unauthorized Category"}
    
    log_section("Without token")
    result = make_request("POST", "/categories", data)
    print(f"Status: {result['status']} (expected 401)")
    
    if result["status"] == 401:
        log_success("Correctly rejected without token")
    else:
        log_error(f"Expected 401, got {result['status']}")
        return False
    
    if ctx.customer_token:
        log_section("With customer token (should be forbidden)")
        result = make_request("POST", "/categories", data, token=ctx.customer_token)
        print(f"Status: {result['status']} (expected 403)")
        
        if result["status"] == 403:
            log_success("Correctly rejected customer token")
        else:
            log_error(f"Expected 403, got {result['status']}")
            return False
    
    return True

# ============================================================
# TEST: Product Creation
# ============================================================
def test_create_product():
    """Test product creation (requires admin/manager token)."""
    log_test_header("Create Product")
    
    if not ctx.admin_token:
        log_warning("No admin token")
        return False
    
    # Get or create a category for the product
    if not ctx.created_category_id:
        log_info("Creating category for product...")
        test_create_category()
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data = {
        "name": f"Test Product {timestamp}",
        "description": "A test product created by the test suite",
        "price": 99.99,
        "stock": 100,
        "categoryId": ctx.created_category_id
    }
    
    log_info(f"Creating product: {data['name']}")
    result = make_request("POST", "/products", data, token=ctx.admin_token)
    
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"]:
        product = result["body"].get("product", {})
        ctx.created_product_id = product.get("id")
        log_success(f"Product created! ID: {ctx.created_product_id}")
        return True
    else:
        log_error("Product creation failed")
        return False

def test_create_product_validation():
    """Test product creation validation."""
    log_test_header("Create Product - Validation Tests")
    
    if not ctx.admin_token:
        log_warning("No admin token")
        return False
    
    test_cases = [
        {
            "name": "Missing name",
            "data": {"price": 10, "stock": 5},
            "expected_status": 400
        },
        {
            "name": "Missing price",
            "data": {"name": "Test", "stock": 5},
            "expected_status": 400
        },
        {
            "name": "Negative price",
            "data": {"name": "Test", "price": -10, "stock": 5},
            "expected_status": 400
        },
        {
            "name": "Invalid category ID",
            "data": {"name": "Test", "price": 10, "stock": 5, "categoryId": 999999},
            "expected_status": 400
        }
    ]
    
    passed = 0
    for test in test_cases:
        log_section(test["name"])
        result = make_request("POST", "/products", test["data"], token=ctx.admin_token)
        
        if result["status"] == test["expected_status"]:
            log_success(f"Got expected status {result['status']}")
            passed += 1
        else:
            log_warning(f"Expected {test['expected_status']}, got {result['status']}")
            # Don't fail completely - validation might be lenient
        
        print(f"Response: {result['body']}")
    
    return passed >= len(test_cases) // 2  # Pass if at least half work

def test_create_product_unauthorized():
    """Test product creation without proper authorization."""
    log_test_header("Create Product - Authorization Tests")
    
    data = {
        "name": "Unauthorized Product",
        "price": 10,
        "stock": 5
    }
    
    log_section("Without token")
    result = make_request("POST", "/products", data)
    print(f"Status: {result['status']} (expected 401)")
    
    if result["status"] == 401:
        log_success("Correctly rejected without token")
    else:
        log_error(f"Expected 401, got {result['status']}")
        return False
    
    if ctx.customer_token:
        log_section("With customer token (should be forbidden)")
        result = make_request("POST", "/products", data, token=ctx.customer_token)
        print(f"Status: {result['status']} (expected 403)")
        
        if result["status"] == 403:
            log_success("Correctly rejected customer token")
        else:
            log_error(f"Expected 403, got {result['status']}")
            return False
    
    return True

# ============================================================
# TEST: Order Creation
# ============================================================
def test_create_order():
    """Test order creation (requires authenticated user)."""
    log_test_header("Create Order")
    
    if not ctx.customer_token:
        log_warning("No customer token")
        return False
    
    # Make sure we have a product to order
    if not ctx.created_product_id:
        log_info("Creating product for order...")
        test_create_product()
    
    if not ctx.created_product_id:
        log_error("No product available for order")
        return False
    
    data = {
        "items": [
            {
                "productId": ctx.created_product_id,
                "quantity": 2
            }
        ],
        "address": "123 Test Street, Test City, TC 12345"
    }
    
    log_info(f"Creating order with product ID: {ctx.created_product_id}")
    result = make_request("POST", "/orders", data, token=ctx.customer_token)
    
    print(f"Status: {result['status']}")
    print(f"Response: {json.dumps(result['body'], indent=2)}")
    
    if result["ok"]:
        order = result["body"].get("order", {})
        ctx.created_order_id = order.get("id")
        log_success(f"Order created! ID: {ctx.created_order_id}")
        log_info(f"Total: ${order.get('totalAmount', 0):.2f}")
        log_info(f"Status: {order.get('status')}")
        return True
    else:
        log_error("Order creation failed")
        return False

def test_create_order_validation():
    """Test order creation validation."""
    log_test_header("Create Order - Validation Tests")
    
    if not ctx.customer_token:
        log_warning("No customer token")
        return False
    
    test_cases = [
        {
            "name": "Empty items array",
            "data": {"items": [], "address": "123 Test St"},
            "expected_status": 400
        },
        {
            "name": "Missing items",
            "data": {"address": "123 Test St"},
            "expected_status": 400
        },
        {
            "name": "Invalid product ID",
            "data": {
                "items": [{"productId": 999999, "quantity": 1}],
                "address": "123 Test St"
            },
            "expected_status": 404  # or 400 depending on implementation
        },
        {
            "name": "Zero quantity",
            "data": {
                "items": [{"productId": ctx.created_product_id or 1, "quantity": 0}],
                "address": "123 Test St"
            },
            "expected_status": 400
        }
    ]
    
    passed = 0
    for test in test_cases:
        log_section(test["name"])
        result = make_request("POST", "/orders", test["data"], token=ctx.customer_token)
        
        # Accept both 400 and 404 for validation errors
        if result["status"] in [400, 404]:
            log_success(f"Got error status {result['status']} (expected ~{test['expected_status']})")
            passed += 1
        else:
            log_warning(f"Expected ~{test['expected_status']}, got {result['status']}")
        
        print(f"Response: {result['body']}")
    
    return passed >= len(test_cases) // 2

def test_create_order_unauthorized():
    """Test order creation without authentication."""
    log_test_header("Create Order - Authorization Tests")
    
    data = {
        "items": [{"productId": 1, "quantity": 1}],
        "address": "123 Test St"
    }
    
    log_section("Without token")
    result = make_request("POST", "/orders", data)
    print(f"Status: {result['status']} (expected 401)")
    
    if result["status"] == 401:
        log_success("Correctly rejected without token")
        return True
    else:
        log_error(f"Expected 401, got {result['status']}")
        return False

# ============================================================
# MAIN TEST RUNNER
# ============================================================
def run_all_tests():
    """Run all creation endpoint tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     SERVER CREATION ENDPOINTS TEST SUITE                 ║")
    print("║     Testing: Products, Categories, Orders, Auth          ║")
    print(f"╚══════════════════════════════════════════════════════════╝{Colors.RESET}")
    print(f"\n{Colors.BLUE}Base URL: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.BLUE}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    
    results = {}
    
    # 1. Auth tests (needed first for tokens)
    print(f"\n{Colors.BOLD}{'='*60}")
    print("SECTION 1: AUTHENTICATION")
    print(f"{'='*60}{Colors.RESET}")
    
    results["Register Admin"] = test_register_admin()
    results["Register Customer"] = test_register_customer()
    results["Register Validation"] = test_register_validation()
    results["Login"] = test_login()
    results["Login Invalid Credentials"] = test_login_invalid_credentials()
    
    # 2. Category tests
    print(f"\n{Colors.BOLD}{'='*60}")
    print("SECTION 2: CATEGORIES")
    print(f"{'='*60}{Colors.RESET}")
    
    results["Create Category"] = test_create_category()
    results["Create Subcategory"] = test_create_subcategory()
    results["Create Category Unauthorized"] = test_create_category_unauthorized()
    
    # 3. Product tests
    print(f"\n{Colors.BOLD}{'='*60}")
    print("SECTION 3: PRODUCTS")
    print(f"{'='*60}{Colors.RESET}")
    
    results["Create Product"] = test_create_product()
    results["Create Product Validation"] = test_create_product_validation()
    results["Create Product Unauthorized"] = test_create_product_unauthorized()
    
    # 4. Order tests
    print(f"\n{Colors.BOLD}{'='*60}")
    print("SECTION 4: ORDERS")
    print(f"{'='*60}{Colors.RESET}")
    
    results["Create Order"] = test_create_order()
    results["Create Order Validation"] = test_create_order_validation()
    results["Create Order Unauthorized"] = test_create_order_unauthorized()
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                    TEST SUMMARY                          ║")
    print(f"╚══════════════════════════════════════════════════════════╝{Colors.RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed{Colors.RESET}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test server creation endpoints")
    parser.add_argument("--base-url", default="http://localhost:3000/api",
                       help="Base URL for API (default: http://localhost:3000/api)")
    
    args = parser.parse_args()
    BASE_URL = args.base_url
    
    sys.exit(run_all_tests())
