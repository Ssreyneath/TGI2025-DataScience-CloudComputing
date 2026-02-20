# Complete E-Commerce Application
from db import *
import streamlit as st
import psycopg2
from psycopg2 import sql
import re
from datetime import datetime, timedelta
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


# ============================================
# STREAMLIT USER INTERFACE
# ============================================

# Page configuration
st.set_page_config(
    page_title="E-Commerce Data Collection",
    page_icon="🛒",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .success-box {
        padding: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database handler
db = ECommerceDB()

def add_customer_page():
    """Customer registration form"""
    st.header("📝 Add New Customer")

    # Use st.form to prevent premature resets
    with st.form("customer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name *", max_chars=50,
                                       help="Enter first name in English or Khmer")
            last_name = st.text_input("Last Name *", max_chars=50,
                                      help="Enter last name in English or Khmer")
            email = st.text_input("Email *", max_chars=100,
                                  placeholder="example@email.com")
            phone = st.text_input("Phone Number *",
                                  placeholder="012 345 678 or +855 12 345 678",
                                  max_chars=20,
                                  help="Cambodian phone number format")

        with col2:
            address = st.text_area("Address *", max_chars=200,
                                   help="Street address, building number, etc.")

            # City dropdown - starts with first city in list
            city_list = sorted(list(CAMBODIA_POSTAL_CODES.keys()))
            city = st.selectbox("City/District *",
                               options=city_list,
                               index=0,  # Default to first city
                               help="Select your city or district")

            # Auto-fill postal code based on city
            auto_postal_code = get_postal_code(city) if city else "120101"
            postal_code = st.text_input("Postal Code *",
                                       value=auto_postal_code,
                                       max_chars=6,
                                       help="Auto-filled based on selected city")

        st.markdown("*Required fields")

        # Form submit button
        submitted = st.form_submit_button("Register Customer", type="primary")

        if submitted:
            # Trim all inputs
            first_name = first_name.strip()
            last_name = last_name.strip()
            email = email.strip()
            phone = phone.strip()
            address = address.strip()
            city = city.strip()
            postal_code = postal_code.strip()

            # Check if any field is empty
            if not first_name:
                st.error("❌ First Name is required")
            elif not last_name:
                st.error("❌ Last Name is required")
            elif not email:
                st.error("❌ Email is required")
            elif not phone:
                st.error("❌ Phone Number is required")
            elif not address:
                st.error("❌ Address is required")
            elif not city:
                st.error("❌ City is required")
            elif not postal_code:
                st.error("❌ Postal Code is required")
            else:
                # All fields filled, proceed with database insertion
                success, message = db.add_customer(
                    first_name, last_name, email, phone, address, city, postal_code
                )

                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")

def create_order_page():
    """Order creation form with category and product selection"""
    st.header("🛍️ Create New Order")

    # Get customers for dropdown
    customers = db.get_customers()
    if not customers:
        st.warning("⚠️ No customers found. Please add a customer first.")
        return

    # Customer selection
    customer_options = {f"{c[1]} {c[2]} ({c[3]})": c[0] for c in customers}
    selected_customer = st.selectbox("Select Customer *", list(customer_options.keys()))
    customer_id = customer_options[selected_customer]

    col1, col2 = st.columns(2)

    with col1:
        # Payment method selection
        payment_methods = db.get_payment_methods()
        payment_options = {pm[1]: pm[0] for pm in payment_methods}
        selected_payment = st.selectbox("Payment Method *", list(payment_options.keys()))
        payment_method_id = payment_options[selected_payment]

    with col2:
        # Channel selection
        channels = db.get_channels()
        channel_options = {f"{ch[1]} - {ch[2]}": ch[0] for ch in channels}
        selected_channel = st.selectbox("Order Channel *", list(channel_options.keys()))
        channel_id = channel_options[selected_channel]

    shipping_address = st.text_area("Shipping Address *", max_chars=200)

    # Order items section
    st.subheader("📦 Add Products to Order")

    # Initialize session state for items
    if 'order_items' not in st.session_state:
        st.session_state.order_items = []

    # Category and Product Selection
    col_cat, col_prod = st.columns(2)

    with col_cat:
        # Get categories
        categories = db.get_product_categories()
        if categories:
            category_options = {f"{cat[1]} - {cat[2]}": cat[0] for cat in categories}
            selected_category = st.selectbox(
                "Select Category",
                list(category_options.keys()),
                key="category_select"
            )
            selected_category_id = category_options[selected_category]
        else:
            st.warning("No product categories found")
            selected_category_id = None

    with col_prod:
        # Get products for selected category
        if selected_category_id:
            products = db.get_products_by_category(selected_category_id)
            if products:
                # Format: "Product Name - $Price (Stock: X)"
                product_options = {
                    f"{p[1]} - ${p[3]:.2f} (Stock: {p[4]})": {
                        'id': p[0],
                        'name': p[1],
                        'price': float(p[3]),
                        'stock': p[4]
                    } for p in products
                }
                selected_product = st.selectbox(
                    "Select Product",
                    list(product_options.keys()),
                    key="product_select"
                )
                product_info = product_options[selected_product]
            else:
                st.warning("No products in this category")
                product_info = None
        else:
            product_info = None

    # Quantity and Add button
    if product_info:
        col_qty, col_btn = st.columns([1, 1])

        with col_qty:
            max_qty = min(product_info['stock'], 1000)  # Limit to stock or 1000
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                max_value=max_qty,
                value=1,
                key="qty",
                help=f"Available stock: {product_info['stock']}"
            )

        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Add to Order", type="primary"):
                if quantity > product_info['stock']:
                    st.error(f"❌ Only {product_info['stock']} items available in stock")
                else:
                    # Check if product already in cart
                    existing_item = None
                    for idx, item in enumerate(st.session_state.order_items):
                        if item['product_name'] == product_info['name']:
                            existing_item = idx
                            break

                    if existing_item is not None:
                        # Update quantity
                        st.session_state.order_items[existing_item]['quantity'] += quantity
                        st.success(f"✅ Updated {product_info['name']} quantity")
                    else:
                        # Add new item
                        st.session_state.order_items.append({
                            'product_name': product_info['name'],
                            'quantity': quantity,
                            'unit_price': product_info['price']
                        })
                        st.success(f"✅ Added {product_info['name']} to order")
                    st.rerun()

    # Display current cart
    if st.session_state.order_items:
        st.markdown("---")
        st.subheader("🛒 Current Order Items")

        total = 0
        for idx, item in enumerate(st.session_state.order_items):
            subtotal = item['quantity'] * item['unit_price']
            total += subtotal

            col_item, col_actions = st.columns([5, 1])

            with col_item:
                st.write(f"**{item['product_name']}**")
                st.write(f"Qty: {item['quantity']} × ${item['unit_price']:.2f} = ${subtotal:.2f}")

            with col_actions:
                if st.button("🗑️", key=f"remove_{idx}", help="Remove item"):
                    st.session_state.order_items.pop(idx)
                    st.rerun()

        st.markdown("---")
        st.markdown(f"### **Total Amount: ${total:.2f}**")

        # Place Order Button
        col_clear, col_order = st.columns([1, 1])

        with col_clear:
            if st.button("🗑️ Clear All Items", type="secondary"):
                st.session_state.order_items = []
                st.rerun()

        with col_order:
            if st.button("✅ Place Order", type="primary"):
                if not shipping_address:
                    st.error("❌ Please enter shipping address")
                elif len(st.session_state.order_items) == 0:
                    st.error("❌ Please add at least one item")
                else:
                    success, message = db.create_order(
                        customer_id, payment_method_id, channel_id,
                        total, shipping_address, st.session_state.order_items
                    )

                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.order_items = []
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    else:
        st.info("ℹ️ No items in order yet. Select a category and product to add.")

def view_customers_page():
    """Display all customers"""
    st.header("👥 Customer List")

    customers = db.get_customers()

    if not customers:
        st.info("No customers found in the database.")
    else:
        st.write(f"Total Customers: {len(customers)}")

        for customer in customers:
            with st.expander(f"Customer ID: {customer[0]} - {customer[1]} {customer[2]}"):
                st.write(f"**Email:** {customer[3]}")
                st.write(f"**Phone:** {customer[4]}")
                st.write(f"**City:** {customer[5]}")

def manage_orders_page():
    """Manage and update order status"""
    st.header("📦 Manage Orders")

    # Get all orders
    orders = db.get_all_orders()

    if not orders:
        st.info("No orders found in the database.")
        return

    st.write(f"Total Orders: {len(orders)}")

    # Display orders in a table format
    for order in orders:
        order_id = order[0]
        order_date = order[1]
        ship_date = order[2]
        status = order[3]
        total = order[4]
        customer_name = f"{order[5]} {order[6]}"
        payment = order[7]
        channel = order[8]

        # Color code by status
        if status == 'Delivered':
            status_color = "🟢"
        elif status == 'Shipped':
            status_color = "🔵"
        elif status == 'Processing':
            status_color = "🟡"
        elif status == 'Cancelled':
            status_color = "🔴"
        else:  # Pending
            status_color = "⚪"

        with st.expander(f"{status_color} Order #{order_id} - {customer_name} - ${total:.2f} - {status}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Order Date:** {order_date}")
                st.write(f"**Ship Date:** {ship_date if ship_date else 'Not shipped yet'}")
                st.write(f"**Customer:** {customer_name}")

            with col2:
                st.write(f"**Status:** {status}")
                st.write(f"**Payment:** {payment}")
                st.write(f"**Channel:** {channel}")

            st.markdown("---")
            st.subheader("Update Order Status")

            # Status update form
            with st.form(f"update_order_{order_id}"):
                col_status, col_date = st.columns(2)

                with col_status:
                    new_status = st.selectbox(
                        "New Status",
                        ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"],
                        index=["Pending", "Processing", "Shipped", "Delivered", "Cancelled"].index(status),
                        key=f"status_{order_id}"
                    )

                with col_date:
                    # Only show ship_date input if status is Shipped or Delivered
                    if new_status in ["Shipped", "Delivered"]:
                        import datetime

                        # Default to current ship_date or today
                        default_date = ship_date if ship_date else datetime.datetime.now()

                        new_ship_date = st.date_input(
                            "Ship Date",
                            value=default_date,
                            min_value=order_date.date() if hasattr(order_date, 'date') else order_date,
                            key=f"ship_date_{order_id}",
                            help="Ship date must be after order date"
                        )
                    else:
                        new_ship_date = None

                submitted = st.form_submit_button("Update Order", type="primary")

                if submitted:
                    # Convert date to datetime if needed
                    if new_ship_date and new_status in ["Shipped", "Delivered"]:
                        import datetime
                        ship_datetime = datetime.datetime.combine(new_ship_date, datetime.time(12, 0))
                    else:
                        ship_datetime = None

                    success, message = db.update_order_status(order_id, new_status, ship_datetime)

                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

def view_order_details_page():
    """View order details (UPDATED to show ship_date)"""
    st.header("📦 Order Details")

    order_id = st.number_input("Enter Order ID", min_value=1, step=1)

    if st.button("Search Order"):
        order_data = db.get_order_details(order_id)

        if not order_data or not order_data['order']:
            st.error("❌ Order not found")
        else:
            order = order_data['order']
            items = order_data['items']

            st.success(f"✅ Order #{order[0]} found")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Order Date:** {order[1]}")
                st.write(f"**Customer:** {order[4]} {order[5]}")
                st.write(f"**Email:** {order[6]}")

            with col2:
                st.write(f"**Status:** {order[3]}")
                st.write(f"**Payment Method:** {order[7]}")
                st.write(f"**Channel:** {order[8]}")

            with col3:
                st.write(f"**Total Amount:** ${order[2]:.2f}")
                # Display ship_date (index 9)
                if order[9]:
                    st.write(f"**Ship Date:** {order[9]}")
                else:
                    st.write(f"**Ship Date:** Not shipped yet")

            st.markdown("---")
            st.subheader("Order Items")

            for item in items:
                st.write(f"• {item[0]} - Qty: {item[1]} × ${item[2]:.2f} = ${item[3]:.2f}")

            st.markdown(f"### **Total: ${order[2]:.2f}**")


def dashboard_page():
    """Analytics Dashboard with charts and data table"""
    st.header("📊 Latest Orders Dashboard")
    
    # Get dashboard statistics
    stats = db.get_dashboard_stats()
    
    if stats:
        # Display KPI metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Revenue", f"${stats['total_revenue']:,.2f}")
        with col2:
            st.metric("Total Orders", f"{stats['total_orders']:,}")
        with col3:
            st.metric("Total Customers", f"{stats['total_customers']:,}")
        with col4:
            st.metric("Avg Order Value", f"${stats['avg_order_value']:,.2f}")
    
    st.markdown("---")
    
    # Charts section
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Revenue by day (from latest 200 orders)")
        
        # Get revenue data
        revenue_data = db.get_revenue_by_day(limit=200)
        
        if revenue_data:
            df_revenue = pd.DataFrame(revenue_data, columns=['date', 'revenue'])
            
            # Create line chart with plotly
            fig_revenue = go.Figure()
            fig_revenue.add_trace(go.Scatter(
                x=df_revenue['date'],
                y=df_revenue['revenue'],
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=8),
                hovertemplate='<b>Date:</b> %{x}<br><b>Revenue:</b> $%{y:.2f}<extra></extra>'
            ))
            
            fig_revenue.update_layout(
                xaxis_title="",
                yaxis_title="",
                hovermode='x unified',
                showlegend=False,
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No revenue data available")
    
    with col_chart2:
        st.subheader("Orders by day (from latest 200 orders)")
        
        # Get orders count data
        orders_data = db.get_orders_by_day(limit=200)
        
        if orders_data:
            df_orders = pd.DataFrame(orders_data, columns=['date', 'order_count'])
            
            # Create bar chart with plotly
            fig_orders = go.Figure()
            fig_orders.add_trace(go.Bar(
                x=df_orders['date'],
                y=df_orders['order_count'],
                name='Orders',
                marker_color='#1f77b4',
                hovertemplate='<b>Date:</b> %{x}<br><b>Orders:</b> %{y}<extra></extra>'
            ))
            
            fig_orders.update_layout(
                xaxis_title="",
                yaxis_title="",
                hovermode='x unified',
                showlegend=False,
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            
            st.plotly_chart(fig_orders, use_container_width=True)
        else:
            st.info("No order data available")
    
    st.markdown("---")
    
    # Data table section
    st.subheader("Latest Orders Table")
    
    # Get latest orders
    orders = db.get_latest_orders_table(limit=200)
    
    if orders:
        # Create DataFrame
        df = pd.DataFrame(orders, columns=[
            'order_id', 'customer_id', 'order_date', 'ship_date', 
            'status', 'category', 'channel', 'total_amount', 
            'discount', 'payment'
        ])
        
        # Format dates
        df['order_date'] = pd.to_datetime(df['order_date']).dt.strftime('%Y-%m-%d')
        df['ship_date'] = df['ship_date'].apply(
            lambda x: pd.to_datetime(x).strftime('%Y-%m-%d') if pd.notna(x) else 'None'
        )
        
        # Format amounts
        df['total_amount'] = df['total_amount'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "$0.00")
        df['discount'] = df['discount'].apply(lambda x: f"${x:.2f}" if pd.notna(x) and x > 0 else "None")
        
        # Rename columns for display
        df = df.rename(columns={
            'order_id': 'Order ID',
            'customer_id': 'Customer ID',
            'order_date': 'Order Date',
            'ship_date': 'Ship Date',
            'status': 'Status',
            'category': 'Category',
            'channel': 'Channel',
            'total_amount': 'Total Amount',
            'discount': 'Discount',
            'payment': 'Payment'
        })
        
        # Display dataframe with custom styling
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"latest_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No orders found in the database")

def main():
    st.title("🛒 E-Commerce Application")
    st.markdown("---")

    menu = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard"
         ,"Add Customer"
          , "Create Order"
          ,"Manage Orders"  # NEW
          , "View Customers"
          , "View Order Details"]
    )

    if menu == "Dashboard":
        dashboard_page()
    elif menu == "Add Customer":
        add_customer_page()
    elif menu == "Create Order":
        create_order_page()
    elif menu == "Manage Orders":
        manage_orders_page()  # NEW
    elif menu == "View Customers":
        view_customers_page()
    elif menu == "View Order Details":
        view_order_details_page()

if __name__ == "__main__":
    main()
