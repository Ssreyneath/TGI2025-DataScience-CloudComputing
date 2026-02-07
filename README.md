
# SampleWebAppWithDatabase - Streamlit Cloud Deployment

## Cloud services used
- SaaS: Jupyter/Colab, GitHub
- PaaS-like: Streamlit Community Cloud
- DBaaS: Neon Postgres

## Deploy steps (students)
1. Create a GitHub repo and upload:
   - app.py
   - db.py
   - requirements.txt
   - .gitignore
   - README.md
2. Streamlit Community Cloud -> New app
   - select repo + branch
   - main file: app.py
3. Streamlit Cloud -> App Settings -> Secrets:
   NEON_DATABASE_URL="postgresql://... ?sslmode=require"
4. Test: submit form -> record appears in table.

## Local run (optional)
pip install -r requirements.txt
export NEON_DATABASE_URL="postgresql://... ?sslmode=require"
streamlit run app.py

# 🛒 E-Commerce Data Collection Application

A comprehensive e-commerce data collection system built with Streamlit and PostgreSQL (Neon).

## Features

- ✅ **Customer Management**: Add and view customer information with validation
- ✅ **Order Processing**: Create orders with product categories and selection
- ✅ **Product Catalog**: Browse products by category with stock tracking
- ✅ **Payment Methods**: Multiple payment options (Credit Card, ABA Pay, Wing, etc.)
- ✅ **Channel Tracking**: Track order sources (Website, Mobile App, Social Media, etc.)
- ✅ **Cambodian Localization**: 
  - Phone number validation (supports +855 and local formats)
  - Postal code auto-fill based on city selection
  - Support for Khmer Unicode characters

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.9+
- **Database**: PostgreSQL (Neon)
- **Libraries**: psycopg2-binary

## Database Schema

### Tables:
- `customers` - Customer information
- `orders` - Order records
- `order_items` - Individual order line items
- `products` - Product catalog
- `product_categories` - Product categories
- `payment_methods` - Available payment options
- `channels` - Order channels/sources

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ecommerce-app.git
cd ecommerce-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.streamlit/secrets.toml` file:
```toml
[database]
host = "your-neon-host.neon.tech"
database = "your_database_name"
user = "your_username"
password = "your_password"
port = "5432"
sslmode = "require"
```

4. Run the application:
```bash
streamlit run app.py
```

## Deployment on Streamlit Community Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add your database credentials in Secrets management
5. Deploy!

## Usage

### Adding a Customer
1. Navigate to "Add Customer" from the sidebar
2. Fill in all required fields
3. Select city (postal code auto-fills)
4. Enter Cambodian phone number in any format
5. Click "Register Customer"

### Creating an Order
1. Navigate to "Create Order"
2. Select customer from dropdown
3. Choose payment method and channel
4. Select product category, then specific product
5. Add items to cart
6. Enter shipping address and place order

## Validation Rules

- **Email**: Valid email format, must be unique
- **Phone**: Cambodian format (0XX XXX XXX or +855 XX XXX XXX)
- **Names**: 2-50 characters, supports Khmer and English
- **Postal Code**: 5-6 digits, auto-filled by city
- **Amount**: Non-negative, max 999,999.99
- **Quantity**: Positive integer, max 1000 or available stock

## Database Setup

Run the SQL scripts in your Neon console to create all necessary tables:
- See `database_schema.sql` for complete table definitions

## Project Structure
```
ecommerce-app/
├── .gitignore          # Git ignore file
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── db.py              # Database operations
└── app.py             # Main application
```

## Contributors

- Your Name - Developer

## License

This project is for educational purposes.

## Support

For issues or questions, please open an issue on GitHub.
