"""Admin modules grouped for the Settings hub (sidebar → Settings)."""

SETTINGS_SECTIONS = [
    {
        'title': 'Security & users',
        'description': 'Accounts, roles, and permissions',
        'items': [
            {'name': 'Users', 'icon': 'bi-person-gear', 'url': '/admin/users/user/', 'code': 'users'},
            {'name': 'Roles', 'icon': 'bi-shield-lock', 'url': '/admin/users/role/', 'code': 'roles'},
            {'name': 'Permissions', 'icon': 'bi-key', 'url': '/admin/users/permission/', 'code': 'permissions'},
            {'name': 'User roles', 'icon': 'bi-person-check', 'url': '/admin/users/userrole/', 'code': 'userroles'},
            {'name': 'Role permissions', 'icon': 'bi-shield-check', 'url': '/admin/users/rolepermission/', 'code': 'rolepermissions'},
        ],
    },
    {
        'title': 'Navigation',
        'description': 'Menus and access mapping',
        'items': [
            {'name': 'Menus', 'icon': 'bi-list-nested', 'url': '/admin/users/menu/', 'code': 'menus'},
            {'name': 'Menu permissions', 'icon': 'bi-link-45deg', 'url': '/admin/users/menupermission/', 'code': 'menupermissions'},
        ],
    },
    {
        'title': 'Organization',
        'description': 'Departments and staff master data',
        'items': [
            {'name': 'Departments', 'icon': 'bi-building', 'url': '/admin/employee/department/', 'code': 'departments'},
            {'name': 'Employees', 'icon': 'bi-people', 'url': '/admin/employee/employee/', 'code': 'employees'},
            {'name': 'Employee cards', 'icon': 'bi-credit-card', 'url': '/admin/employee/employeecard/', 'code': 'cards'},
        ],
    },
    {
        'title': 'Inventory & menu',
        'description': 'Food catalog and stock',
        'items': [
            {'name': 'Food categories', 'icon': 'bi-tags', 'url': '/admin/inventory/foodcategory/', 'code': 'categories'},
            {'name': 'Menu items', 'icon': 'bi-cup-hot', 'url': '/admin/inventory/menuitem/', 'code': 'menuitems'},
            {'name': 'Daily stock', 'icon': 'bi-calendar-day', 'url': '/admin/inventory/dailyfoodstock/', 'code': 'dailystock'},
            {'name': 'Suppliers', 'icon': 'bi-shop', 'url': '/admin/inventory/supplier/', 'code': 'suppliers'},
            {'name': 'Raw materials', 'icon': 'bi-basket', 'url': '/admin/inventory/rawmaterial/', 'code': 'rawmaterials'},
            {'name': 'Material stock', 'icon': 'bi-boxes', 'url': '/admin/inventory/rawmaterialstock/', 'code': 'rawstock'},
            {'name': 'Waste records', 'icon': 'bi-trash', 'url': '/admin/inventory/wasterecord/', 'code': 'waste'},
        ],
    },
    {
        'title': 'Balance & sales',
        'description': 'Balances, orders, and payments',
        'items': [
            {'name': 'Employee balances', 'icon': 'bi-wallet2', 'url': '/admin/balance/employeebalance/', 'code': 'balances'},
            {'name': 'Balance allocations', 'icon': 'bi-cash-stack', 'url': '/admin/balance/balanceallocation/', 'code': 'allocations'},
            {'name': 'Monthly allowances', 'icon': 'bi-calendar-month', 'url': '/admin/balance/monthlyallowance/', 'code': 'allowances'},
            {'name': 'Credit limits', 'icon': 'bi-credit-card-2-front', 'url': '/admin/balance/creditlimit/', 'code': 'creditlimits'},
            {'name': 'Card transactions', 'icon': 'bi-receipt', 'url': '/admin/balance/cardtransaction/', 'code': 'transactions'},
            {'name': 'Orders', 'icon': 'bi-bag-check', 'url': '/admin/pos/order/', 'code': 'orders'},
            {'name': 'Payments', 'icon': 'bi-currency-dollar', 'url': '/admin/pos/payment/', 'code': 'payments'},
            {'name': 'Guest cards', 'icon': 'bi-person-badge', 'url': '/admin/pos/guestcard/', 'code': 'guestcards'},
        ],
    },
    {
        'title': 'System',
        'description': 'Configuration and audit trail',
        'items': [
            {'name': 'System settings', 'icon': 'bi-sliders', 'url': '/admin/core/systemsetting/', 'code': 'systemsettings'},
            {'name': 'Audit logs', 'icon': 'bi-journal-text', 'url': '/admin/core/auditlog/', 'code': 'auditlogs'},
            {'name': 'Django admin (full)', 'icon': 'bi-gear-wide-connected', 'url': '/admin/', 'code': 'django_admin'},
        ],
    },
]
