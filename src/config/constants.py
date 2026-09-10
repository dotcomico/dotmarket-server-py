ROLES = {
    'ADMIN': 'admin',
    'MANAGER': 'manager',
    'CUSTOMER': 'customer'
}

ORDER_STATUS = {
    'PENDING': 'pending',
    'PAID': 'paid',
    'SHIPPED': 'shipped',
    'CANCELLED': 'cancelled'
}

# Inventory: a product is "low stock" when stock is strictly below this.
# Out-of-stock rows (stock <= 0) are therefore also counted as low stock —
# this matches what the admin dashboard has always displayed.
LOW_STOCK_THRESHOLD = 10

# Order statuses that count as *realized* revenue. Single home for this
# definition so the admin dashboard's "Total Revenue" tile and the per-user
# `totalSpent` column can never drift apart. Pending/cancelled are excluded.
REVENUE_STATUSES = (ORDER_STATUS['PAID'], ORDER_STATUS['SHIPPED'])

# How many low-stock products the dashboard's "Low Stock Alert" panel previews.
# The panel shows "<preview> of <lowStockCount>", so this caps the list only —
# never the count.
LOW_STOCK_PREVIEW_LIMIT = 5
