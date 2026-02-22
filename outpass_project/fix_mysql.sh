#!/bin/bash

# Quick MySQL Fix Script
# Run this script to create a MySQL user for the Outpass system

echo "=========================================="
echo "MySQL Quick Fix for Outpass System"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Create database 'outpass_clean' (if not exists)"
echo "2. Create MySQL user 'outpass_user' with password 'Outpass@1234'"
echo "3. Grant all permissions on outpass_clean database"
echo "4. Import schema and dummy data"
echo ""
read -p "Press Enter to continue (or Ctrl+C to cancel)..."

# Create database and user
echo ""
echo "Creating database and user..."
sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS outpass_clean;
CREATE USER IF NOT EXISTS 'outpass_user'@'localhost' IDENTIFIED BY 'Outpass@1234';
GRANT ALL PRIVILEGES ON outpass_clean.* TO 'outpass_user'@'localhost';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database and user created successfully!"
    echo ""
    echo "Importing schema..."
    mysql -u outpass_user -p'Outpass@1234' < schema.sql
    
    echo "Importing dummy data..."
    mysql -u outpass_user -p'Outpass@1234' < dummy_data.sql
    
    echo ""
    echo "=========================================="
    echo "✅ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Your start.sh already has the correct credentials!"
    echo "Just run: ./start.sh"
    echo ""
    echo "Then restart your server!"
else
    echo "❌ Failed to create user. Make sure you have sudo access."
fi
