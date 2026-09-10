#!/usr/bin/env python3
"""
=============================================================================
🛒 SUPERMARKET DATABASE SEED FILE
=============================================================================
This script populates your Flask supermarket database with realistic test data.

Run this AFTER deleting your existing database file.

Usage:
    cd backend
    python seed_database.py

Test Users:
    - Admin:    admin@test.com    / password: Test123!
    - Manager:  manager@test.com  / password: Test123!
    - Customer: customer@test.com / password: Test123!
=============================================================================
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add the backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
import bcrypt
from src.config.database import db, connectDB
from src.models.User import User
from src.models.Category import Category
from src.models.Product import Product
from src.models.Order import Order
from src.models.OrderItem import OrderItem

# =============================================================================
# CONFIGURATION
# =============================================================================
PASSWORD = "Test123!"  # Same password for all test users

# =============================================================================
# CATEGORY DATA - Realistic Supermarket Hierarchy
# =============================================================================
CATEGORIES = [
    # Parent Categories (id will be assigned sequentially starting from 1)
    {"name": "Fruits & Vegetables", "icon": "🥬", "parent": None},      # 1
    {"name": "Meat & Poultry", "icon": "🥩", "parent": None},           # 2
    {"name": "Fish & Seafood", "icon": "🐟", "parent": None},           # 3
    {"name": "Dairy & Eggs", "icon": "🥛", "parent": None},             # 4
    {"name": "Bakery", "icon": "🍞", "parent": None},                   # 5
    {"name": "Pantry & Dry Goods", "icon": "🫙", "parent": None},       # 6
    {"name": "Snacks & Sweets", "icon": "🍫", "parent": None},          # 7
    {"name": "Beverages", "icon": "🥤", "parent": None},                # 8
    {"name": "Frozen Foods", "icon": "🧊", "parent": None},             # 9
    {"name": "Household & Cleaning", "icon": "🧹", "parent": None},     # 10
    {"name": "Personal Care", "icon": "🧴", "parent": None},            # 11
    {"name": "Electronics", "icon": "🔌", "parent": None},              # 12
    
    # Subcategories - Fruits & Vegetables (parent=1)
    {"name": "Fresh Fruits", "icon": "🍎", "parent": 1},                # 13
    {"name": "Fresh Vegetables", "icon": "🥕", "parent": 1},            # 14
    {"name": "Dried Fruits & Nuts", "icon": "🥜", "parent": 1},         # 15
    {"name": "Organic Produce", "icon": "🌿", "parent": 1},             # 16
    
    # Subcategories - Meat & Poultry (parent=2)
    {"name": "Beef", "icon": "🐄", "parent": 2},                        # 17
    {"name": "Chicken", "icon": "🐔", "parent": 2},                     # 18
    {"name": "Pork", "icon": "🐷", "parent": 2},                        # 19
    {"name": "Lamb", "icon": "🐑", "parent": 2},                        # 20
    
    # Subcategories - Fish & Seafood (parent=3)
    {"name": "Fresh Fish", "icon": "🐠", "parent": 3},                  # 21
    {"name": "Shellfish", "icon": "🦐", "parent": 3},                   # 22
    {"name": "Smoked & Cured", "icon": "🐟", "parent": 3},              # 23
    
    # Subcategories - Dairy & Eggs (parent=4)
    {"name": "Milk & Cream", "icon": "🥛", "parent": 4},                # 24
    {"name": "Cheese", "icon": "🧀", "parent": 4},                      # 25
    {"name": "Yogurt", "icon": "🥣", "parent": 4},                      # 26
    {"name": "Eggs", "icon": "🥚", "parent": 4},                        # 27
    {"name": "Butter & Margarine", "icon": "🧈", "parent": 4},          # 28
    
    # Subcategories - Bakery (parent=5)
    {"name": "Bread & Rolls", "icon": "🍞", "parent": 5},               # 29
    {"name": "Pastries & Cakes", "icon": "🥐", "parent": 5},            # 30
    {"name": "Cookies & Biscuits", "icon": "🍪", "parent": 5},          # 31
    
    # Subcategories - Pantry & Dry Goods (parent=6)
    {"name": "Rice & Grains", "icon": "🍚", "parent": 6},               # 32
    {"name": "Pasta & Noodles", "icon": "🍝", "parent": 6},             # 33
    {"name": "Canned Goods", "icon": "🥫", "parent": 6},                # 34
    {"name": "Oils & Vinegars", "icon": "🫒", "parent": 6},             # 35
    {"name": "Spices & Seasonings", "icon": "🌶️", "parent": 6},         # 36
    {"name": "Breakfast & Cereals", "icon": "🥣", "parent": 6},         # 37
    
    # Subcategories - Snacks & Sweets (parent=7)
    {"name": "Chips & Crisps", "icon": "🍟", "parent": 7},              # 38
    {"name": "Candy & Chocolate", "icon": "🍬", "parent": 7},           # 39
    {"name": "Nuts & Seeds", "icon": "🥜", "parent": 7},                # 40
    {"name": "Ice Cream", "icon": "🍦", "parent": 7},                   # 41
    
    # Subcategories - Beverages (parent=8)
    {"name": "Water & Sparkling", "icon": "💧", "parent": 8},           # 42
    {"name": "Soft Drinks", "icon": "🥤", "parent": 8},                 # 43
    {"name": "Juices", "icon": "🧃", "parent": 8},                      # 44
    {"name": "Coffee & Tea", "icon": "☕", "parent": 8},                # 45
    {"name": "Energy Drinks", "icon": "⚡", "parent": 8},               # 46
    
    # Subcategories - Frozen Foods (parent=9)
    {"name": "Frozen Vegetables", "icon": "🥦", "parent": 9},           # 47
    {"name": "Frozen Meals", "icon": "🍱", "parent": 9},                # 48
    {"name": "Frozen Pizza", "icon": "🍕", "parent": 9},                # 49
    {"name": "Frozen Desserts", "icon": "🍨", "parent": 9},             # 50
    
    # Subcategories - Household & Cleaning (parent=10)
    {"name": "Laundry", "icon": "🧺", "parent": 10},                    # 51
    {"name": "Dish Care", "icon": "🍽️", "parent": 10},                  # 52
    {"name": "Surface Cleaners", "icon": "🧽", "parent": 10},           # 53
    {"name": "Paper Products", "icon": "🧻", "parent": 10},             # 54
    
    # Subcategories - Personal Care (parent=11)
    {"name": "Body Care", "icon": "🛁", "parent": 11},                  # 55
    {"name": "Hair Care", "icon": "💇", "parent": 11},                  # 56
    {"name": "Oral Care", "icon": "🦷", "parent": 11},                  # 57
    
    # Subcategories - Electronics (parent=12)
    {"name": "Smart Devices", "icon": "📱", "parent": 12},              # 58
    {"name": "Audio", "icon": "🎧", "parent": 12},                      # 59
    {"name": "Cameras & Accessories", "icon": "📷", "parent": 12},      # 60
]

# =============================================================================
# PRODUCT DATA - From Old DB + New Products
# =============================================================================
PRODUCTS = [
    # === FROM OLD DATABASE (with images) ===
    {
        "name": "Apple",
        "description": "Fresh apples are crisp, juicy, and nutritious fruits, with popular varieties including Honeycrisp, Gala, Fuji, Pink Lady, and Granny Smith. They are a great source of fiber, vitamin C, and antioxidants like quercetin.",
        "price": 2.99,
        "stock": 150,
        "categoryId": 13,  # Fresh Fruits
        "image": "/uploads/1769813340619.png",
        "image360": "/uploads/1769813340627.gif"
    },
    {
        "name": "Banana",
        "description": "The best bananas from Africa. Sweet, creamy, and packed with potassium. Perfect for smoothies, baking, or as a healthy snack.",
        "price": 1.49,
        "stock": 200,
        "categoryId": 13,  # Fresh Fruits
        "image": "/uploads/1769468094211.png",
        "image360": "/uploads/1769881778440.gif"
    },
    {
        "name": "Peanut Butter - Nuttie's Creamy",
        "description": "Smooth creamy Peanut Butter made from premium roasted peanuts. No added sugar, no palm oil. Perfect for sandwiches and baking.",
        "price": 6.99,
        "stock": 85,
        "categoryId": 40,  # Nuts & Seeds
        "image": "/uploads/1769468730141.png",
        "image360": "/uploads/1769881503508.gif"
    },
    {
        "name": "Coffee Beans - Explorer's Blend",
        "description": "High-altitude Arabica beans with notes of dark chocolate and toasted hazelnuts. Medium-Dark Roast, roasted in small batches for peak freshness.",
        "price": 14.99,
        "stock": 75,
        "categoryId": 45,  # Coffee & Tea
        "image": "/uploads/1769469144089.png",
        "image360": "/uploads/1769881853355.gif"
    },
    {
        "name": "Evergreen Elixir - Cold-Pressed Green Juice",
        "description": "A refreshing blend of kale, spinach, green apple, and ginger. No added sugar, just pure liquid vitality.",
        "price": 6.00,
        "stock": 45,
        "categoryId": 44,  # Juices
        "image": "/uploads/1769469221098.png",
        "image360": "/uploads/1769881897325.gif"
    },
    {
        "name": "Laundry Detergent - Ocean Fresh Ultra Clean",
        "description": "A powerful, eco-friendly detergent that removes tough stains while leaving your clothes with a crisp, sea-breeze scent.",
        "price": 12.50,
        "stock": 120,
        "categoryId": 51,  # Laundry
        "image": "/uploads/1769469285745.png",
        "image360": "/uploads/1769882129873.gif"
    },
    {
        "name": "Sunrise Granola - Honey & Walnut Clusters",
        "description": "Crunchy toasted oats glazed with organic honey and tossed with premium walnut halves and cinnamon.",
        "price": 8.95,
        "stock": 60,
        "categoryId": 37,  # Breakfast & Cereals
        "image": "/uploads/1769469355038.png",
        "image360": "/uploads/1769882168627.gif"
    },
    {
        "name": "Citrus Spark - Natural Dish Soap",
        "description": "A grease-cutting formula powered by eucalyptus and lemongrass essential oils. Gentle on hands, tough on grime.",
        "price": 5.25,
        "stock": 200,
        "categoryId": 52,  # Dish Care
        "image": "/uploads/1769469417061.png",
        "image360": "/uploads/1769882193837.gif"
    },
    {
        "name": "Ice Cream - Moonlight Swirl Lavender Honeycomb",
        "description": "Gourmet lavender-infused cream with crunchy honeycomb bits and a golden honey swirl. A dream in every scoop.",
        "price": 7.50,
        "stock": 35,
        "categoryId": 41,  # Ice Cream
        "image": "/uploads/1769469478987.png",
        "image360": "/uploads/1769882207898.gif"
    },
    {
        "name": "Oro Verde Extra Virgin Olive Oil",
        "description": "Cold-pressed from early-harvest Koroneiki olives. Features a peppery finish and a vibrant, grassy aroma.",
        "price": 19.00,
        "stock": 90,
        "categoryId": 35,  # Oils & Vinegars
        "image": "/uploads/1769469537576.png",
        "image360": "/uploads/1769882253787.gif"
    },
    {
        "name": "Botanical Bliss - Handmade Soap Bar",
        "description": "An artisanal soap bar crafted with lavender, sage, and exfoliating oats for a calming and skin-softening wash.",
        "price": 6.50,
        "stock": 150,
        "categoryId": 55,  # Body Care
        "image": "/uploads/1769469606814.png",
        "image360": "/uploads/1769881527403.gif"
    },
    {
        "name": "Premium Black Angus Ribeye Steak",
        "description": "A thick, hand-cut ribeye steak featuring exceptional marbling for a buttery texture and rich flavor. Perfect for grilling or pan-searing.",
        "price": 24.99,
        "stock": 25,
        "categoryId": 17,  # Beef
        "image": "/uploads/1769470050305.png",
        "image360": "/uploads/1769881632587.gif"
    },
    {
        "name": "Horizon Smart Hub & Speaker",
        "description": "A sleek, voice-controlled smart home assistant with a vibrant circular display. Manages your schedule, music, and smart devices with ease.",
        "price": 129.00,
        "stock": 15,
        "categoryId": 58,  # Smart Devices
        "image": "/uploads/1769470111007.png",
        "image360": "/uploads/1769881790205.gif"
    },
    {
        "name": "Titan X Wireless Charging Stand",
        "description": "A high-speed 15W wireless charger with a minimalist aluminum design. Keeps your phone upright at the perfect viewing angle while charging.",
        "price": 45.00,
        "stock": 50,
        "categoryId": 58,  # Smart Devices
        "image": "/uploads/1769470155472.png",
        "image360": "/uploads/1769881802554.gif"
    },
    {
        "name": "Pulse Pro Fitness Smartwatch",
        "description": "Tracks heart rate, sleep quality, and over 50 workout types. Features a curved AMOLED display and a 10-day battery life.",
        "price": 199.00,
        "stock": 30,
        "categoryId": 58,  # Smart Devices
        "image": "/uploads/1769470190198.png",
        "image360": "/uploads/1769881816325.gif"
    },
    {
        "name": "NeoPodz Noise-Canceling Earbuds",
        "description": "True wireless earbuds with active noise cancellation and a smart charging case that displays battery life and time.",
        "price": 149.00,
        "stock": 40,
        "categoryId": 59,  # Audio
        "image": "/uploads/1769470228332.png",
        "image360": "/uploads/1769881829037.gif"
    },
    {
        "name": "VisionX VR Pro Headset",
        "description": "Immersive 4K virtual reality headset with built-in spatial audio and ergonomic head straps for long gaming sessions.",
        "price": 499.00,
        "stock": 8,
        "categoryId": 58,  # Smart Devices
        "image": "/uploads/1769470283202.png",
        "image360": "/uploads/1769871476128.gif"
    },
    {
        "name": "Lumix SLR Digital Camera (Professional Bundle)",
        "description": "High-resolution DSLR camera with a 24.2MP sensor, including a 24-70mm lens and a high-speed 128GB memory card.",
        "price": 1250.00,
        "stock": 3,  # LOW STOCK - for dashboard testing
        "categoryId": 60,  # Cameras & Accessories
        "image": "/uploads/1769470326740.png",
        "image360": "/uploads/1769871463277.gif"
    },
    {
        "name": "Mushroom Savory Pastry",
        "description": "A flaky, golden-brown puff pastry filled with a savory blend of sautéed forest mushrooms, caramelized onions, and a touch of black pepper.",
        "price": 2.50,
        "stock": 80,
        "categoryId": 30,  # Pastries & Cakes
        "image": "/uploads/1769871423513.png",
        "image360": "/uploads/1769871423542.gif"
    },
    {
        "name": "Fresh Atlantic Salmon Fillet",
        "description": "Premium, skin-on Atlantic salmon known for its vibrant color and rich, buttery texture. High in Omega-3 fatty acids and perfect for pan-searing or roasting.",
        "price": 14.99,
        "stock": 45,
        "categoryId": 21,  # Fresh Fish
        "image": "/uploads/1769896297733.png",
        "image360": "/uploads/1769896297759.gif"
    },
    
    # === NEW PRODUCTS (No images - system will use placeholders) ===
    # Fresh Vegetables (14)
    {
        "name": "Organic Carrots (1lb)",
        "description": "Sweet, crunchy organic carrots. Perfect for snacking, cooking, or juicing.",
        "price": 2.49,
        "stock": 120,
        "categoryId": 14,
        "image": "/uploads/1770118479222.png",
        "image360": "/uploads/1770118479230.gif"
    },
    {
        "name": "Fresh Broccoli",
        "description": "Vibrant green broccoli florets, packed with vitamins and fiber.",
        "price": 2.99,
        "stock": 80,
        "categoryId": 14,
        "image": "/uploads/1770118503393.png",
        "image360": "/uploads/1770118503401.gif"
    },
    {
        "name": "Red Bell Peppers (3-pack)",
        "description": "Sweet, crisp red bell peppers. Great for salads, stir-fries, or stuffing.",
        "price": 4.99,
        "stock": 5,  # LOW STOCK
        "categoryId": 14,
        "image": "/uploads/1770118604977.png",
        "image360": "/uploads/1770118604984.gif"
    },

    # Dried Fruits & Nuts (15)
    {
        "name": "Roasted Almonds (12oz)",
        "description": "Lightly salted roasted almonds. A protein-rich snack.",
        "price": 8.99,
        "stock": 65,
        "categoryId": 15,
        "image": "/uploads/1770118658734.png",
        "image360": "/uploads/1770118658742.gif"
    },
    {
        "name": "Dried Mango Slices",
        "description": "No sugar added dried mango slices. Tropical sweetness in every bite.",
        "price": 5.99,
        "stock": 40,
        "categoryId": 15,
        "image": "/uploads/1770118691792.png",
        "image360": "/uploads/1770118691799.gif"
    },

    # Chicken (18)
    {
        "name": "Free-Range Chicken Breast (2-pack)",
        "description": "Boneless, skinless chicken breasts from free-range chickens. Lean and versatile.",
        "price": 12.99,
        "stock": 55,
        "categoryId": 18,
        "image": "/uploads/1770118751901.png",
        "image360": "/uploads/1770118751908.gif"
    },
    {
        "name": "Organic Whole Chicken",
        "description": "Whole organic chicken, perfect for roasting. Approximately 4-5 lbs.",
        "price": 18.99,
        "stock": 20,
        "categoryId": 18,
        "image": "/uploads/1770118824041.png",
        "image360": "/uploads/1770118824048.gif"
    },
    
    # Shellfish (22)
    {
        "name": "Jumbo Shrimp (1lb)",
        "description": "Wild-caught jumbo shrimp, peeled and deveined. Ready to cook.",
        "price": 16.99,
        "stock": 30,
        "categoryId": 22,
        "image": None,
        "image360": None
    },
    
    # Milk & Cream (24)
    {
        "name": "Whole Milk (1 Gallon)",
        "description": "Farm-fresh whole milk. Rich, creamy, and perfect for the whole family.",
        "price": 4.49,
        "stock": 100,
        "categoryId": 24,
        "image": None,
        "image360": None
    },
    {
        "name": "Heavy Whipping Cream",
        "description": "Ultra-pasteurized heavy cream for whipping, cooking, and baking.",
        "price": 5.99,
        "stock": 45,
        "categoryId": 24,
        "image": None,
        "image360": None
    },
    
    # Cheese (25)
    {
        "name": "Aged Cheddar Cheese Block",
        "description": "Sharp, aged cheddar with complex flavor. Aged 12 months.",
        "price": 7.99,
        "stock": 60,
        "categoryId": 25,
        "image": None,
        "image360": None
    },
    {
        "name": "Fresh Mozzarella Ball",
        "description": "Creamy Italian mozzarella, perfect for caprese salad or pizza.",
        "price": 6.49,
        "stock": 35,
        "categoryId": 25,
        "image": None,
        "image360": None
    },
    
    # Yogurt (26)
    {
        "name": "Greek Yogurt - Plain (32oz)",
        "description": "Thick, protein-rich Greek yogurt. No added sugar.",
        "price": 5.99,
        "stock": 80,
        "categoryId": 26,
        "image": None,
        "image360": None
    },
    
    # Eggs (27)
    {
        "name": "Free-Range Large Eggs (12-pack)",
        "description": "Farm-fresh free-range eggs. Rich golden yolks.",
        "price": 5.99,
        "stock": 150,
        "categoryId": 27,
        "image": None,
        "image360": None
    },
    {
        "name": "Organic Brown Eggs (18-pack)",
        "description": "Certified organic brown eggs from pasture-raised hens.",
        "price": 8.99,
        "stock": 2,  # LOW STOCK
        "categoryId": 27,
        "image": None,
        "image360": None
    },
    
    # Bread & Rolls (29)
    {
        "name": "Artisan Sourdough Loaf",
        "description": "Crusty sourdough bread with a tangy flavor and chewy crumb. Baked fresh daily.",
        "price": 5.99,
        "stock": 40,
        "categoryId": 29,
        "image": None,
        "image360": None
    },
    {
        "name": "Whole Wheat Sandwich Bread",
        "description": "100% whole wheat bread with no artificial preservatives.",
        "price": 3.99,
        "stock": 75,
        "categoryId": 29,
        "image": None,
        "image360": None
    },
    
    # Pastries & Cakes (30)
    {
        "name": "Butter Croissant (4-pack)",
        "description": "Flaky, buttery French croissants. Perfect for breakfast.",
        "price": 6.99,
        "stock": 25,
        "categoryId": 30,
        "image": None,
        "image360": None
    },
    
    # Rice & Grains (32)
    {
        "name": "Basmati Rice (2lb)",
        "description": "Premium aged basmati rice with a delicate aroma and fluffy texture.",
        "price": 6.99,
        "stock": 90,
        "categoryId": 32,
        "image": None,
        "image360": None
    },
    {
        "name": "Organic Quinoa",
        "description": "Pre-washed organic quinoa. High protein, gluten-free superfood.",
        "price": 7.99,
        "stock": 55,
        "categoryId": 32,
        "image": None,
        "image360": None
    },
    
    # Pasta & Noodles (33)
    {
        "name": "Italian Spaghetti",
        "description": "Traditional bronze-cut spaghetti made from durum wheat semolina.",
        "price": 2.99,
        "stock": 200,
        "categoryId": 33,
        "image": None,
        "image360": None
    },
    {
        "name": "Penne Rigate",
        "description": "Ridged penne pasta, perfect for holding chunky sauces.",
        "price": 2.99,
        "stock": 180,
        "categoryId": 33,
        "image": None,
        "image360": None
    },
    
    # Canned Goods (34)
    {
        "name": "San Marzano Tomatoes",
        "description": "Imported Italian whole peeled tomatoes. The gold standard for pasta sauce.",
        "price": 4.99,
        "stock": 120,
        "categoryId": 34,
        "image": None,
        "image360": None
    },
    {
        "name": "Organic Black Beans",
        "description": "Ready-to-use organic black beans. Low sodium.",
        "price": 2.49,
        "stock": 150,
        "categoryId": 34,
        "image": None,
        "image360": None
    },
    
    # Chips & Crisps (38)
    {
        "name": "Sea Salt Kettle Chips",
        "description": "Crunchy kettle-cooked potato chips with sea salt.",
        "price": 4.49,
        "stock": 100,
        "categoryId": 38,
        "image": None,
        "image360": None
    },
    {
        "name": "Organic Tortilla Chips",
        "description": "Stone-ground organic corn tortilla chips. Perfect with salsa.",
        "price": 3.99,
        "stock": 85,
        "categoryId": 38,
        "image": None,
        "image360": None
    },
    
    # Candy & Chocolate (39)
    {
        "name": "Dark Chocolate Bar (72% Cacao)",
        "description": "Premium Belgian dark chocolate. Rich, intense flavor.",
        "price": 4.99,
        "stock": 70,
        "categoryId": 39,
        "image": None,
        "image360": None
    },
    {
        "name": "Gummy Bears (1lb)",
        "description": "Classic fruit-flavored gummy bears. A nostalgic treat.",
        "price": 5.99,
        "stock": 60,
        "categoryId": 39,
        "image": None,
        "image360": None
    },
    
    # Water & Sparkling (42)
    {
        "name": "Spring Water (24-pack)",
        "description": "Natural spring water from mountain sources. 16.9oz bottles.",
        "price": 5.99,
        "stock": 200,
        "categoryId": 42,
        "image": None,
        "image360": None
    },
    {
        "name": "Sparkling Water Variety Pack",
        "description": "Assorted fruit-flavored sparkling water. No sugar, no calories.",
        "price": 7.99,
        "stock": 150,
        "categoryId": 42,
        "image": None,
        "image360": None
    },
    
    # Soft Drinks (43)
    {
        "name": "Cola Classic (12-pack)",
        "description": "Classic cola in 12oz cans. Refreshing and iconic.",
        "price": 6.99,
        "stock": 180,
        "categoryId": 43,
        "image": None,
        "image360": None
    },
    
    # Energy Drinks (46)
    {
        "name": "Energy Boost - Original (4-pack)",
        "description": "Energy drink with caffeine, B-vitamins, and taurine.",
        "price": 8.99,
        "stock": 0,  # OUT OF STOCK
        "categoryId": 46,
        "image": None,
        "image360": None
    },
    
    # Frozen Vegetables (47)
    {
        "name": "Frozen Mixed Vegetables",
        "description": "A blend of peas, carrots, corn, and green beans. Flash-frozen for freshness.",
        "price": 3.49,
        "stock": 90,
        "categoryId": 47,
        "image": None,
        "image360": None
    },
    
    # Frozen Pizza (49)
    {
        "name": "Margherita Pizza",
        "description": "Stone-baked pizza with tomato sauce, mozzarella, and fresh basil.",
        "price": 8.99,
        "stock": 45,
        "categoryId": 49,
        "image": None,
        "image360": None
    },
    {
        "name": "Pepperoni Pizza",
        "description": "Classic pepperoni pizza with extra cheese. Family size.",
        "price": 9.99,
        "stock": 50,
        "categoryId": 49,
        "image": None,
        "image360": None
    },
    
    # Surface Cleaners (53)
    {
        "name": "All-Purpose Cleaner Spray",
        "description": "Multi-surface cleaner that cuts through grease and grime. Fresh lemon scent.",
        "price": 4.99,
        "stock": 110,
        "categoryId": 53,
        "image": None,
        "image360": None
    },
    
    # Paper Products (54)
    {
        "name": "Paper Towels (6-roll pack)",
        "description": "Super absorbent paper towels. 2-ply, select-a-size sheets.",
        "price": 9.99,
        "stock": 75,
        "categoryId": 54,
        "image": None,
        "image360": None
    },
    {
        "name": "Toilet Paper (12-pack)",
        "description": "Soft, strong 2-ply toilet paper. Septic-safe.",
        "price": 12.99,
        "stock": 4,  # LOW STOCK
        "categoryId": 54,
        "image": None,
        "image360": None
    },
    
    # Hair Care (56)
    {
        "name": "Moisturizing Shampoo",
        "description": "Gentle daily shampoo with argan oil for soft, shiny hair.",
        "price": 8.99,
        "stock": 65,
        "categoryId": 56,
        "image": None,
        "image360": None
    },
    {
        "name": "Conditioner - Deep Repair",
        "description": "Intensive conditioner for damaged hair. With keratin protein.",
        "price": 9.99,
        "stock": 55,
        "categoryId": 56,
        "image": None,
        "image360": None
    },
    
    # Oral Care (57)
    {
        "name": "Whitening Toothpaste",
        "description": "Fluoride toothpaste that whitens teeth and freshens breath.",
        "price": 4.99,
        "stock": 120,
        "categoryId": 57,
        "image": None,
        "image360": None
    },

    # === PRODUCTS ADDED VIA ADMIN PANEL (post-seed) ===

    # Snacks & Sweets (7)
    {
        "name": "Proar Protein Bar",
        "description": "A premium energy bar featuring dark chocolate chunks, whole almonds, and hazelnuts.",
        "price": 2.49,
        "stock": 1000,
        "categoryId": 7,
        "image": "/uploads/1770122332810.png",
        "image360": "/uploads/1770122332817.gif"
    },
    {
        "name": "Energy Boost Bar",
        "description": "A crunchy granola bar packed with roasted peanuts and chocolate chips, designed for a quick energy lift.",
        "price": 1.89,
        "stock": 1000,
        "categoryId": 7,
        "image": "/uploads/1770122407831.png",
        "image360": "/uploads/1770122407837.gif"
    },
    {
        "name": "Choc-Top Pop!",
        "description": "Fluffy popcorn kernels fully coated in a rich, smooth milk chocolate glaze.",
        "price": 4.50,
        "stock": 500,
        "categoryId": 7,
        "image": "/uploads/1770122729238.png",
        "image360": "/uploads/1770122729244.gif"
    },

    # Chips & Crisps (38)
    {
        "name": "Crunchy Waves",
        "description": "Classic ridged potato chips flavored with sour cream and garden onion.",
        "price": 3.50,
        "stock": 500,
        "categoryId": 38,
        "image": "/uploads/1770122492850.png",
        "image360": "/uploads/1770122492858.gif"
    },
    {
        "name": "Pretzel Twists",
        "description": "Oven-baked traditional pretzel knots seasoned with classic sea salt.",
        "price": 2.99,
        "stock": 500,
        "categoryId": 38,
        "image": "/uploads/1770122552828.png",
        "image360": "/uploads/1770122552834.gif"
    },
    {
        "name": "Spicy Crunch",
        "description": "Zesty corn tortilla chips flavored with sharp cheddar cheese and a kick of jalapeño pepper.",
        "price": 3.25,
        "stock": 500,
        "categoryId": 38,
        "image": "/uploads/1770122639968.png",
        "image360": "/uploads/1770122639981.gif"
    },

    # Candy & Chocolate (39)
    {
        "name": "Island Fruits",
        "description": "A mix of premium dried tropical fruits, including pineapple, mango, and kiwi chunks.",
        "price": 5.99,
        "stock": 600,
        "categoryId": 39,
        "image": "/uploads/1770122831989.png",
        "image360": "/uploads/1770122831995.gif"
    },
    {
        "name": "Zingy Tangs (Bag)",
        "description": "A colorful variety of chewy gummy candies coated in an extra-sour crystalline sugar.",
        "price": 2.75,
        "stock": 600,
        "categoryId": 39,
        "image": "/uploads/1770122887395.png",
        "image360": "/uploads/1770122887403.gif"
    },
    {
        "name": "Zingy Tangs (Canister)",
        "description": "The signature sour fruit gummies are packaged in a reusable, eco-friendly cylindrical tin.",
        "price": 4.99,
        "stock": 500,
        "categoryId": 39,
        "image": "/uploads/1770122965611.png",
        "image360": "/uploads/1770122965618.gif"
    },

    # Dish Care (52)
    {
        "name": "Ocean Fresh Ultra-Clean™ Dishwasher Detergent Gel",
        "description": "Concentrated Deep Clean Formula | Streak-Free Shine | Easy-Dose Bottle\n\nBring the purifying power of the sea to your kitchen with Ocean Fresh Ultra-Clean® Dishwasher Detergent Gel. This high-performance liquid detergent is specifically engineered to tackle the toughest kitchen challenges, from dried-on proteins to stubborn grease.\n\nSpotless Technology: Formulated to prevent water spots and filming on glassware.\nRapid Dissolve: Optimized for both heavy-duty and eco-friendly short cycles.\nMachine Care: Helps prevent limescale buildup, extending the life of your dishwasher.",
        "price": 12.90,
        "stock": 700,
        "categoryId": 52,
        "image": "/uploads/1770123952375.png",
        "image360": "/uploads/1770123952382.gif"
    },

    # Coffee & Tea (45)
    {
        "name": "Aurora Ethiopian Whole Bean Coffee",
        "description": "A medium-roast specialty coffee with notes of citrus and floral jasmine. Sourced directly from Ethiopian highlands for a smooth and sophisticated morning cup.",
        "price": 15.99,
        "stock": 100,
        "categoryId": 45,
        "image": "/uploads/1770124669671.png",
        "image360": "/uploads/1770124669677.gif"
    },

    # Ice Cream (41)
    {
        "name": "Lavender Bloom Artisanal Ice Cream",
        "description": "A gourmet pint of creamy lavender-infused ice cream with a luscious blackberry swirl. Made with 100% organic cream and natural botanical extracts.",
        "price": 5.49,
        "stock": 100,
        "categoryId": 41,
        "image": "/uploads/1770124757077.png",
        "image360": "/uploads/1770124757110.gif"
    },

    # Juices (44)
    {
        "name": "Green Revive Cold-Pressed Superfood Juice",
        "description": "A refreshing blend of kale, spinach, green apple, ginger, and lemon. Cold-pressed to retain maximum nutrients and vitamins with no added sugar.",
        "price": 4.99,
        "stock": 200,
        "categoryId": 44,
        "image": "/uploads/1770124876647.png",
        "image360": "/uploads/1770124876654.gif"
    },

    # Breakfast & Cereals (37)
    {
        "name": "Sunrise Artisanal Honey & Almond Granola",
        "description": "Crunchy clusters of whole-grain oats toasted with organic honey, roasted almonds, and golden raisins. High in fiber and naturally sweetened.",
        "price": 6.29,
        "stock": 150,
        "categoryId": 37,
        "image": "/uploads/1770124984124.png",
        "image360": "/uploads/1770124984132.gif"
    },

    # Cheese (25)
    {
        "name": "Rolling Hills Aged English Cheddar",
        "description": "A sharp, crumbly cheddar aged for 12 months for a deep, complex flavor profile. Hand-wrapped in parchment, perfect for cheese boards and wine pairings.",
        "price": 7.99,
        "stock": 20,
        "categoryId": 25,
        "image": "/uploads/1770125125655.png",
        "image360": "/uploads/1770125125663.gif"
    },
    {
        "name": "Meadow Morn Small Curd Cottage Cheese",
        "description": "High-protein, all-natural cottage cheese with a smooth texture and small curds. Made with real farm milk.",
        "price": 4.10,
        "stock": 500,
        "categoryId": 25,
        "image": "/uploads/1770125874478.png",
        "image360": "/uploads/1770125874481.gif"
    },
    {
        "name": "Creamy Fields Herb & Garlic Spread",
        "description": "A velvety cream cheese spread infused with fresh herbs and roasted garlic. Perfect for bagels or crackers.",
        "price": 4.62,
        "stock": 100,
        "categoryId": 25,
        "image": "/uploads/1770126011976.png",
        "image360": "/uploads/1770126011978.gif"
    },

    # Yogurt (26)
    {
        "name": "Velvet Dairy Blueberry Greek Yogurt",
        "description": "Rich and creamy probiotic Greek yogurt with a luscious blueberry swirl and oat clusters. Comes in a premium glass jar.",
        "price": 5.50,
        "stock": 40,
        "categoryId": 26,
        "image": "/uploads/1770125593629.png",
        "image360": "/uploads/1770125593634.gif"
    },

    # Milk & Cream (24)
    {
        "name": "Oatscape Barista Blend Oat Milk",
        "description": "Organic, naturally lactose-free oat milk designed for coffee. Creates a perfect micro-foam for lattes and cappuccinos.",
        "price": 4.90,
        "stock": 300,
        "categoryId": 24,
        "image": "/uploads/1770125711178.png",
        "image360": None
    },
    {
        "name": "Morning Dew Organic Whole Milk",
        "description": "Farm-fresh organic whole milk served in a traditional glass bottle to preserve its pure and rich taste.",
        "price": 6.20,
        "stock": 600,
        "categoryId": 24,
        "image": "/uploads/1770125791273.png",
        "image360": "/uploads/1770125791274.gif"
    },

    # Eggs (27)
    {
        "name": "Sunrise Farms Organic Brown Eggs",
        "description": "A carton of farm-fresh, free-range organic brown eggs. Rich in protein and Omega-3 with deep orange yolks.",
        "price": 7.48,
        "stock": 0,  # OUT OF STOCK
        "categoryId": 27,
        "image": "/uploads/1770126104767.png",
        "image360": "/uploads/1770126104770.gif"
    },

    # Pantry & Dry Goods (6)
    {
        "name": "Terra Cold-Pressed Extra-Virgin Oil Infused with Kalamata Olives &",
        "description": "A high-quality, cold-pressed extra-virgin olive oil sourced from Greece. This oil is infused with whole Kalamata olives and fresh rosemary sprigs, creating a rich, aromatic, Mediterranean flavor profile. The bottle includes a seal for protected origin.",
        "price": 19.99,
        "stock": 100,
        "categoryId": 6,
        "image": "/uploads/1770126840242.png",
        "image360": "/uploads/1770126840244.gif"
    },

    # Body Care (55)
    {
        "name": "Fresh Bloom Moisturizing Hand Soap with Natural Extracts",
        "description": "A hydrating liquid hand soap featuring natural botanical extracts and a peony blossom fragrance. The formulation is designed to cleanse hands while leaving them soft, moisturized, and pleasantly scented. It is presented in a clear bottle with a bamboo pump dispenser and includes a small, complementary solid soap bar sample.",
        "price": 9.99,
        "stock": 400,
        "categoryId": 55,
        "image": "/uploads/1770126971967.png",
        "image360": "/uploads/1770126971969.gif"
    },
]

# =============================================================================
# USER DATA
# =============================================================================
USERS = [
    {
        "username": "Sarah Chen",
        "email": "admin@test.com",
        "role": "admin"
    },
    {
        "username": "Marcus Webb",
        "email": "manager@test.com",
        "role": "manager"
    },
    # Primary demo customer — keeps the documented `customer@test.com`
    # credential (see docs/QUICK_START.md) and owns the bulk of the order
    # history so `/orders` and the admin tables have a real customer to show.
    {
        "username": "Elena Rodriguez",
        "email": "customer@test.com",
        "role": "customer"
    },
    # Additional customers exist only to populate the admin User/Order tables
    # (§9 W2) — not documented login credentials, but same Test123! password.
    {
        "username": "Priya Patel",
        "email": "priya.patel@test.com",
        "role": "customer"
    },
    {
        "username": "James Carter",
        "email": "james.carter@test.com",
        "role": "customer"
    },
    {
        "username": "Mia Thompson",
        "email": "mia.thompson@test.com",
        "role": "customer"
    },
    {
        "username": "David Kim",
        "email": "david.kim@test.com",
        "role": "customer"
    },
    {
        "username": "Olivia Brooks",
        "email": "olivia.brooks@test.com",
        "role": "customer"
    },
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_app_for_seed():
    """Create a minimal Flask app for database seeding."""
    from dotenv import load_dotenv
    load_dotenv()
    
    # 1. חישוב הנתיב האבסולוטי לתיקייה שבה אנחנו נמצאים כרגע (root)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 2. הגדרת הנתיב המדויק ל-src/instance
    instance_path = os.path.join(base_dir, 'src', 'instance')
    
    # יצירת התיקייה אם היא לא קיימת
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)

    # 3. יצירת האפליקציה תוך הגדרה מפורשת של ה-instance_path
    # זה מונע מ-Flask לנחש איפה לשים דברים
    app = Flask(__name__, instance_path=instance_path)
    
    # 4. בניית הנתיב לקובץ הדאטהבייס
    db_file_path = os.path.join(instance_path, 'database.sqlite')
    
    # --- תיקון קריטי ל-Windows ---
    # מחליף backslash (\) ב-forward slash (/) כדי ש-SQLAlchemy יקרא את זה נכון
    db_file_path = db_file_path.replace('\\', '/')
    
    # 5. הגדרת ה-URI הסופי
    # שים לב לשימוש ב-3 סלשים (///) לנתיב אבסולוטי
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print(f"📍 Database path forced to: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    connectDB(app)
    return app

def clear_database():
    """Clear all tables in the correct order to respect foreign keys."""
    print("🗑️  Creating tables (if needed)...")
    db.create_all()
    
    print("🗑️  Clearing existing data...")
    OrderItem.query.delete()
    Order.query.delete()
    Product.query.delete()
    Category.query.delete()
    User.query.delete()
    db.session.commit()
    print("✅ Database cleared")

def seed_users():
    """Create test users with hashed passwords.

    `users_map["customer"]` stays the single primary demo customer (backward
    compatible with anything keying off that), while `users_map["customers"]`
    is the full ordered list of customer users — seed_orders() spreads orders
    across all of them instead of piling every order onto one account (§9 W2).
    """
    print("\n👤 Creating users...")
    users_map = {"customers": []}

    # Hash password using bcrypt (same as your auth_controller)
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(PASSWORD.encode('utf-8'), salt).decode('utf-8')

    for user_data in USERS:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password=hashed_password,
            role=user_data["role"]
        )
        db.session.add(user)
        db.session.flush()  # Get the ID
        if user_data["role"] == "customer":
            users_map.setdefault("customer", user)  # first one = primary
            users_map["customers"].append(user)
        else:
            users_map[user_data["role"]] = user
        print(f"   ✅ Created {user_data['role']}: {user_data['username']} <{user_data['email']}>")

    db.session.commit()
    return users_map

def seed_categories():
    """Create category hierarchy."""
    print("\n📁 Creating categories...")
    category_map = {}
    
    for i, cat_data in enumerate(CATEGORIES, start=1):
        category = Category(
            name=cat_data["name"],
            icon=cat_data["icon"],
            parentId=cat_data["parent"]
        )
        db.session.add(category)
        db.session.flush()
        category_map[i] = category
    
    db.session.commit()
    
    # Count parents and children
    parents = len([c for c in CATEGORIES if c["parent"] is None])
    children = len([c for c in CATEGORIES if c["parent"] is not None])
    print(f"   ✅ Created {parents} parent categories")
    print(f"   ✅ Created {children} subcategories")
    
    return category_map

def seed_products():
    """Create products with various stock levels."""
    print("\n📦 Creating products...")
    product_list = []
    
    for prod_data in PRODUCTS:
        product = Product(
            name=prod_data["name"],
            description=prod_data["description"],
            price=prod_data["price"],
            stock=prod_data["stock"],
            categoryId=prod_data["categoryId"],
            image=prod_data.get("image"),
            image360=prod_data.get("image360")
        )
        db.session.add(product)
        db.session.flush()
        product_list.append(product)
    
    db.session.commit()
    
    # Stats
    total = len(product_list)
    with_images = len([p for p in PRODUCTS if p.get("image")])
    low_stock = len([p for p in PRODUCTS if 0 < p["stock"] <= 5])
    out_of_stock = len([p for p in PRODUCTS if p["stock"] == 0])
    
    print(f"   ✅ Created {total} products")
    print(f"   📸 {with_images} with images")
    print(f"   ⚠️  {low_stock} with low stock (≤5)")
    print(f"   ❌ {out_of_stock} out of stock")
    
    return product_list

def _create_order(customer, address, status, days_ago, items):
    """Local (seed-only) helper. `items` is a list of (product, quantity)
    tuples. `createdAt`/`updatedAt` are set explicitly (days before "now")
    instead of the model's `server_default=now()` so seeded orders land on
    distinct dates spread over the last month rather than all sharing one
    seed-run timestamp (§9 W1)."""
    placed_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_ago)
    order = Order(
        totalAmount=0,
        status=status,
        address=address,
        UserId=customer.id,
        createdAt=placed_at,
        updatedAt=placed_at,
    )
    db.session.add(order)
    db.session.flush()

    total = 0
    for product, quantity in items:
        price = product.price
        db.session.add(OrderItem(
            OrderId=order.id,
            ProductId=product.id,
            quantity=quantity,
            priceAtPurchase=price
        ))
        total += price * quantity
    order.totalAmount = round(total, 2)
    return order


def seed_orders(users_map, products):
    """Create sample orders spread across every seeded customer (§9 W2) with
    createdAt dates spread over the last ~30 days (§9 W1), real addresses
    matching each customer's own name (§9 W3), and a mix of every status."""
    print("\n🛒 Creating orders...")

    elena, priya, james, mia, david, olivia = users_map["customers"]

    # (customer, address, status, days_ago, [(product, quantity), ...])
    orders_spec = [
        # Elena Rodriguez — primary demo account (customer@test.com), 5 orders
        (elena, "Elena Rodriguez, 123 Main Street\nApt 4B, New York, NY 10001, Phone: 555-0123",
         "shipped", 28, [(products[0], 3), (products[1], 2), (products[6], 1)]),
        (elena, "Elena Rodriguez, 123 Main Street\nApt 4B, New York, NY 10001, Phone: 555-0123",
         "paid", 21, [(products[11], 1), (products[9], 1), (products[19], 1)]),
        (elena, "Elena Rodriguez, 123 Main Street\nApt 4B, New York, NY 10001, Phone: 555-0123",
         "pending", 12, [(products[12], 1), (products[15], 1)]),
        (elena, "Elena Rodriguez, 456 Oak Avenue\nSuite 100, Los Angeles, CA 90001, Phone: 555-0456",
         "cancelled", 6, [(products[16], 1)]),
        (elena, "Elena Rodriguez, 789 Elm Street\nFloor 2, Chicago, IL 60601, Phone: 555-0789",
         "shipped", 1, [(products[5], 2), (products[7], 3), (products[10], 2)]),

        # Priya Patel — 3 orders
        (priya, "Priya Patel, 22 Birchwood Lane, Seattle, WA 98101, Phone: 555-0291",
         "shipped", 25, [(products[3], 2), (products[37], 1)]),
        (priya, "Priya Patel, 22 Birchwood Lane, Seattle, WA 98101, Phone: 555-0291",
         "paid", 14, [(products[14], 1), (products[13], 1)]),
        (priya, "Priya Patel, 22 Birchwood Lane, Seattle, WA 98101, Phone: 555-0291",
         "pending", 3, [(products[35], 1), (products[30], 1), (products[32], 2)]),

        # James Carter — 2 orders
        (james, "James Carter, 88 Cedar Ridge Road, Austin, TX 73301, Phone: 555-0345",
         "paid", 19, [(products[17], 1)]),
        (james, "James Carter, 88 Cedar Ridge Road, Austin, TX 73301, Phone: 555-0345",
         "shipped", 5, [(products[25], 2), (products[26], 1), (products[38], 1)]),

        # Mia Thompson — 2 orders
        (mia, "Mia Thompson, 14 Willow Creek Drive, Denver, CO 80202, Phone: 555-0412",
         "pending", 16, [(products[61], 5), (products[62], 5)]),
        (mia, "Mia Thompson, 14 Willow Creek Drive, Denver, CO 80202, Phone: 555-0412",
         "shipped", 2, [(products[48], 2), (products[49], 1), (products[50], 1)]),

        # David Kim — 2 orders
        (david, "David Kim, 501 Harbor View Boulevard, Miami, FL 33101, Phone: 555-0567",
         "paid", 9, [(products[60], 2), (products[58], 1), (products[59], 1)]),
        (david, "David Kim, 501 Harbor View Boulevard, Miami, FL 33101, Phone: 555-0567",
         "cancelled", 0, [(products[15], 1), (products[13], 1)]),

        # Olivia Brooks — 1 order
        (olivia, "Olivia Brooks, 76 Maple Grove Court, Portland, OR 97201, Phone: 555-0678",
         "shipped", 23, [(products[75], 2), (products[76], 3), (products[77], 2)]),
    ]

    status_counts = {}
    max_days_ago = 0
    for customer, address, status, days_ago, items in orders_spec:
        _create_order(customer, address, status, days_ago, items)
        status_counts[status] = status_counts.get(status, 0) + 1
        max_days_ago = max(max_days_ago, days_ago)

    db.session.commit()

    print(f"   ✅ Created {len(orders_spec)} orders across {len(users_map['customers'])} customers, "
          f"dated over the last {max_days_ago} days:")
    for status, count in sorted(status_counts.items()):
        print(f"      - {count} {status}")

def print_summary():
    """Print final summary with login credentials."""
    print("\n" + "=" * 60)
    print("🎉 DATABASE SEEDED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📊 Summary:")
    print(f"   • Categories: {Category.query.count()}")
    print(f"   • Products: {Product.query.count()}")
    print(f"   • Users: {User.query.count()}")
    print(f"   • Orders: {Order.query.count()}")
    
    print("\n🔐 Test User Credentials:")
    print("   ┌─────────────────────────────────────────────────┐")
    print("   │ Role      │ Email              │ Password       │")
    print("   ├─────────────────────────────────────────────────┤")
    print("   │ Admin     │ admin@test.com     │ Test123!       │")
    print("   │ Manager   │ manager@test.com   │ Test123!       │")
    print("   │ Customer  │ customer@test.com  │ Test123!       │")
    print("   └─────────────────────────────────────────────────┘")
    
    print("\n⚠️  Dashboard Test Scenarios:")
    print("   • Low stock products: Check Products page for items with stock ≤ 5")
    print("   • Out of stock: At least 1 product with 0 stock")
    print("   • Order statuses: pending, paid, shipped, cancelled")
    print("   • Orders: 15 orders across 6 customers, dated over the last ~28 days")
    print("   • customer@test.com (Elena Rodriguez) owns 5 of them for the /orders demo")
    
    print("\n🚀 Start your server with: python -m src.main")
    print("=" * 60)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main seeding function."""
    print("=" * 60)
    print("🌱 SUPERMARKET DATABASE SEEDER")
    print("=" * 60)
    
    app = create_app_for_seed()
    
    with app.app_context():
        # Clear existing data
        clear_database()
        
        # Seed in order
        users_map = seed_users()
        seed_categories()
        products = seed_products()
        seed_orders(users_map, products)
        
        # Print summary
        print_summary()

if __name__ == "__main__":
    main()