# Set environment variable from Colab secrets
import os
import streamlit as st
import psycopg2
from psycopg2 import sql

# ============================================
# DATABASE CONFIGURATION
# ============================================
# Use environment variable for database URL
DB_URL = os.environ.get('NEON_DATABASE_URL')

def get_db_connection():
    """Establish database connection"""
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# ============================================
# DATA VALIDATION CLASS
# ============================================
"""
Database configuration and operations for E-Commerce Application
"""

import psycopg2
from psycopg2 import sql
import streamlit as st
import re

def get_db_connection():
    """
    Establish database connection using Streamlit secrets
    """
    try:
        # Use Streamlit secrets for deployment
        conn = psycopg2.connect(
            host=st.secrets["database"]["host"],
            database=st.secrets["database"]["database"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            port=st.secrets["database"]["port"],
            sslmode=st.secrets["database"]["sslmode"]
        )
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None


class DataValidator:
    """Validation rules for all input fields"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, "Valid"
    
    @staticmethod
    def validate_phone(phone):
        """Validate Cambodian phone number format"""
        cleaned_phone = re.sub(r'[\s\-()]', '', phone)
        
        pattern1 = r'^0(1[0-9]|6[1-9]|7[0-9]|8[1-9]|9[0-9])\d{6,7}$'
        pattern2 = r'^\+855(1[0-9]|6[1-9]|7[0-9]|8[1-9]|9[0-9])\d{6,7}$'
        pattern3 = r'^855(1[0-9]|6[1-9]|7[0-9]|8[1-9]|9[0-9])\d{6,7}$'
        
        if re.match(pattern1, cleaned_phone) or re.match(pattern2, cleaned_phone) or re.match(pattern3, cleaned_phone):
            return True, "Valid"
        else:
            return False, "Invalid Cambodian phone number. Format: 0XX XXX XXX or +855 XX XXX XXX"
    
    @staticmethod
    def validate_name(name, field_name="Name"):
        """Validate name fields - Simple and reliable"""
        if not name or len(name.strip()) < 2:
            return False, f"{field_name} must be at least 2 characters"
        if len(name) > 50:
            return False, f"{field_name} cannot exceed 50 characters"
        
        cleaned_name = name.strip()
        
        # Only block numbers - allow all letters
        if any(char.isdigit() for char in cleaned_name):
            return False, f"{field_name} cannot contain numbers"
        
        return True, "Valid"
    
    @staticmethod
    def validate_postal_code(postal_code):
        """Validate postal code (Cambodia format)"""
        if not postal_code or len(postal_code.strip()) < 5:
            return False, "Postal code must be at least 5 characters"
        if len(postal_code) > 6:
            return False, "Postal code cannot exceed 6 characters"
        
        cleaned_code = postal_code.strip()
        
        if not cleaned_code.isdigit():
            return False, "Postal code must contain only digits"
        
        if len(cleaned_code) not in [5, 6]:
            return False, "Postal code must be 5-6 digits"
        
        return True, "Valid"
    
    @staticmethod
    def validate_amount(amount):
        """Validate monetary amount"""
        try:
            amount_float = float(amount)
            if amount_float < 0:
                return False, "Amount cannot be negative"
            if amount_float > 999999.99:
                return False, "Amount exceeds maximum limit"
            return True, "Valid"
        except ValueError:
            return False, "Invalid amount format"
    
    @staticmethod
    def validate_quantity(quantity):
        """Validate product quantity"""
        try:
            qty = int(quantity)
            if qty <= 0:
                return False, "Quantity must be greater than 0"
            if qty > 1000:
                return False, "Quantity cannot exceed 1000"
            return True, "Valid"
        except ValueError:
            return False, "Quantity must be a number"
    
    @staticmethod
    def validate_ship_date(order_date, ship_date):
        """Validate that ship_date is after order_date"""
        from datetime import datetime
        
        try:
            if ship_date is None:
                return True, "Valid"
            
            if isinstance(order_date, str):
                order_date = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
            if isinstance(ship_date, str):
                ship_date = datetime.fromisoformat(ship_date.replace('Z', '+00:00'))
            
            if ship_date < order_date:
                return False, "Ship date cannot be before order date"
            
            return True, "Valid"
        except Exception as e:
            return False, f"Invalid date format: {str(e)}"


class ECommerceDB:
    """Handle all database operations"""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def add_customer(self, first_name, last_name, email, phone, address, city, postal_code):
        """Add a new customer with validation"""
        
        validations = [
            self.validator.validate_name(first_name, "First name"),
            self.validator.validate_name(last_name, "Last name"),
            self.validator.validate_email(email),
            self.validator.validate_phone(phone),
            self.validator.validate_postal_code(postal_code)
        ]
        
        for is_valid, message in validations:
            if not is_valid:
                return False, message
        
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO customers (first_name, last_name, email, phone, address, city, postal_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING customer_id
            """
            cursor.execute(query, (first_name, last_name, email, phone, address, city, postal_code))
            customer_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"Customer added successfully! ID: {customer_id}"
        except psycopg2.errors.UndefinedTable as e:
            conn.rollback()
            conn.close()
            return False, "Database table 'customers' does not exist. Please create the tables first."
        except psycopg2.IntegrityError as e:
            conn.rollback()
            conn.close()
            error_msg = str(e)
            if 'email' in error_msg or 'unique' in error_msg.lower():
                return False, f"Email '{email}' already exists in the system"
            else:
                return False, f"Database constraint violation: {error_msg}"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Error adding customer: {type(e).__name__} - {str(e)}"
    
    def create_order(self, customer_id, payment_method_id, channel_id, 
                     total_amount, shipping_address, items):
        """Create a new order with items"""
        
        is_valid, message = self.validator.validate_amount(total_amount)
        if not is_valid:
            return False, message
        
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            
            order_query = """
                INSERT INTO orders (customer_id, payment_method_id, channel_id, 
                                   total_amount, shipping_address)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING order_id
            """
            cursor.execute(order_query, (customer_id, payment_method_id, channel_id, 
                                        total_amount, shipping_address))
            order_id = cursor.fetchone()[0]
            
            for item in items:
                is_valid, msg = self.validator.validate_quantity(item['quantity'])
                if not is_valid:
                    raise ValueError(msg)
                
                is_valid, msg = self.validator.validate_amount(item['unit_price'])
                if not is_valid:
                    raise ValueError(msg)
                
                item_query = """
                    INSERT INTO order_items (order_id, product_name, quantity, 
                                            unit_price, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """
                subtotal = item['quantity'] * item['unit_price']
                cursor.execute(item_query, (order_id, item['product_name'], 
                                          item['quantity'], item['unit_price'], subtotal))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"Order created successfully! Order ID: {order_id}"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Error creating order: {str(e)}"
    
    def get_payment_methods(self):
        """Retrieve all active payment methods"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT payment_method_id, method_name FROM payment_methods WHERE is_active = TRUE")
            methods = cursor.fetchall()
            cursor.close()
            conn.close()
            return methods
        except Exception as e:
            st.error(f"Error fetching payment methods: {e}")
            return []
    
    def get_channels(self):
        """Retrieve all channels"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT channel_id, channel_name, description FROM channels")
            channels = cursor.fetchall()
            cursor.close()
            conn.close()
            return channels
        except Exception as e:
            st.error(f"Error fetching channels: {e}")
            return []
    
    def get_customers(self):
        """Retrieve all customers"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT customer_id, first_name, last_name, email, phone, city 
                FROM customers 
                ORDER BY created_at DESC
            """)
            customers = cursor.fetchall()
            cursor.close()
            conn.close()
            return customers
        except Exception as e:
            st.error(f"Error fetching customers: {e}")
            return []
    
    def get_order_details(self, order_id):
        """Retrieve order details with items"""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            order_query = """
                SELECT o.order_id, o.order_date, o.total_amount, o.order_status,
                       c.first_name, c.last_name, c.email,
                       pm.method_name, ch.channel_name, o.ship_date
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                JOIN payment_methods pm ON o.payment_method_id = pm.payment_method_id
                JOIN channels ch ON o.channel_id = ch.channel_id
                WHERE o.order_id = %s
            """
            cursor.execute(order_query, (order_id,))
            order = cursor.fetchone()
            
            items_query = """
                SELECT product_name, quantity, unit_price, subtotal
                FROM order_items
                WHERE order_id = %s
            """
            cursor.execute(items_query, (order_id,))
            items = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {'order': order, 'items': items}
        except Exception as e:
            st.error(f"Error fetching order details: {e}")
            return None
    
    def get_product_categories(self):
        """Retrieve all active product categories"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category_id, category_name, description 
                FROM product_categories 
                WHERE is_active = TRUE 
                ORDER BY category_name
            """)
            categories = cursor.fetchall()
            cursor.close()
            conn.close()
            return categories
        except Exception as e:
            st.error(f"Error fetching categories: {e}")
            return []
    
    def get_products_by_category(self, category_id):
        """Retrieve all active products for a specific category"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id, product_name, description, unit_price, stock_quantity
                FROM products 
                WHERE category_id = %s AND is_active = TRUE 
                ORDER BY product_name
            """, (category_id,))
            products = cursor.fetchall()
            cursor.close()
            conn.close()
            return products
        except Exception as e:
            st.error(f"Error fetching products: {e}")
            return []
    
    def get_all_orders(self):
        """Retrieve all orders with summary information"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.ship_date, o.order_status, 
                       o.total_amount, c.first_name, c.last_name,
                       pm.method_name, ch.channel_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                JOIN payment_methods pm ON o.payment_method_id = pm.payment_method_id
                JOIN channels ch ON o.channel_id = ch.channel_id
                ORDER BY o.order_date DESC
            """)
            orders = cursor.fetchall()
            cursor.close()
            conn.close()
            return orders
        except Exception as e:
            st.error(f"Error fetching orders: {e}")
            return []
    
    def update_order_status(self, order_id, new_status, ship_date=None):
        """Update order status and ship_date with validation"""
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT order_date, order_status 
                FROM orders 
                WHERE order_id = %s
            """, (order_id,))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                return False, "Order not found"
            
            order_date, current_status = result
            
            if ship_date:
                is_valid, message = self.validator.validate_ship_date(order_date, ship_date)
                if not is_valid:
                    cursor.close()
                    conn.close()
                    return False, message
                
                query = """
                    UPDATE orders 
                    SET order_status = %s, ship_date = %s 
                    WHERE order_id = %s
                """
                cursor.execute(query, (new_status, ship_date, order_id))
            else:
                query = """
                    UPDATE orders 
                    SET order_status = %s 
                    WHERE order_id = %s
                """
                cursor.execute(query, (new_status, order_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"Order #{order_id} updated to '{new_status}'"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Error updating order: {str(e)}"
    
    def get_revenue_by_day(self, limit=200):
        """Get daily revenue from latest orders"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    DATE(order_date) as date,
                    SUM(total_amount) as revenue
                FROM (
                    SELECT order_date, total_amount
                    FROM orders
                    ORDER BY order_date DESC
                    LIMIT %s
                ) as latest_orders
                GROUP BY DATE(order_date)
                ORDER BY date
            """, (limit,))
            
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return data
        except Exception as e:
            st.error(f"Error fetching revenue data: {e}")
            return []
    
    def get_orders_by_day(self, limit=200):
        """Get order count by day from latest orders"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    DATE(order_date) as date,
                    COUNT(*) as order_count
                FROM (
                    SELECT order_date
                    FROM orders
                    ORDER BY order_date DESC
                    LIMIT %s
                ) as latest_orders
                GROUP BY DATE(order_date)
                ORDER BY date
            """, (limit,))
            
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return data
        except Exception as e:
            st.error(f"Error fetching order count data: {e}")
            return []
    
    def get_latest_orders_table(self, limit=200):
        """Get latest orders for table display"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT
                    o.order_id,
                    CONCAT('cust-', LPAD(c.customer_id::text, 3, '0')) as customer_id,
                    o.order_date,
                    o.ship_date,
                    o.order_status as status,
                    COALESCE(pc.category_name, 'N/A') as category,
                    ch.channel_name as channel,
                    o.total_amount,
                    COALESCE(o.discount, 0) as discount,
                    pm.method_name as payment
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                JOIN channels ch ON o.channel_id = ch.channel_id
                JOIN payment_methods pm ON o.payment_method_id = pm.payment_method_id
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                LEFT JOIN products p ON oi.product_name = p.product_name
                LEFT JOIN product_categories pc ON p.category_id = pc.category_id
                ORDER BY o.order_date DESC
                LIMIT %s
            """, (limit,))
            
            orders = cursor.fetchall()
            cursor.close()
            conn.close()
            return orders
        except Exception as e:
            st.error(f"Error fetching latest orders: {e}")
            return []
    
    def get_dashboard_stats(self):
        """Get summary statistics for dashboard"""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders")
            total_revenue = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM customers")
            total_customers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(AVG(total_amount), 0) FROM orders")
            avg_order_value = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT order_status, COUNT(*) 
                FROM orders 
                GROUP BY order_status
            """)
            orders_by_status = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'total_customers': total_customers,
                'avg_order_value': float(avg_order_value),
                'orders_by_status': orders_by_status
            }
        except Exception as e:
            st.error(f"Error fetching dashboard stats: {e}")
            return None


# Cambodia Postal Code Database
CAMBODIA_POSTAL_CODES = {
    "Phnom Penh": "120101",
    "Khan Chamkar Mon": "120101",
    "Khan Doun Penh": "120201",
    "Khan 7 Makara": "120301",
    "Khan Toul Kork": "120401",
    "Khan Dangkao": "120501",
    "Khan Mean Chey": "120601",
    "Khan Russey Keo": "120701",
    "Khan Sen Sok": "120801",
    "Khan Pou Senchey": "120901",
    "Khan Chroy Changvar": "121001",
    "Khan Prampir Meakkakra": "121101",
    "Khan Chbar Ampov": "121201",
    "Khan Boeng Keng Kang": "121301",
    "Khan Kamboul": "121401",
    "Siem Reap": "170101",
    "Battambang": "020101",
    "Kampong Cham": "030101",
    "Sihanoukville": "180101",
    "Preah Sihanouk": "180101",
    "Kandal": "080101",
    "Ta Khmau": "080101",
    "Kampot": "070101",
    "Kep": "230101",
    "Takeo": "210101",
    "Kampong Speu": "050101",
    "Kampong Thom": "060101",
    "Kampong Chhnang": "040101",
    "Pursat": "150101",
    "Koh Kong": "090101",
    "Kratié": "100101",
    "Mondulkiri": "110101",
    "Ratanakiri": "160101",
    "Stung Treng": "190101",
    "Preah Vihear": "130101",
    "Oddar Meanchey": "220101",
    "Banteay Meanchey": "010101",
    "Pailin": "240101",
}


def get_postal_code(city):
    """Get postal code based on city name"""
    if city in CAMBODIA_POSTAL_CODES:
        return CAMBODIA_POSTAL_CODES[city]
    
    for key, value in CAMBODIA_POSTAL_CODES.items():
        if key.lower() == city.lower():
            return value
    
    return "120101"
