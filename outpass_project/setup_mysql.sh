#!/bin/bash

# MySQL Setup Script for Outpass Management System
# This script helps set up MySQL authentication

echo "=========================================="
echo "MySQL Setup for Outpass Management System"
echo "=========================================="
echo ""

# Check if MySQL is running
if ! systemctl is-active --quiet mysql 2>/dev/null && ! systemctl is-active --quiet mysqld 2>/dev/null; then
    echo "⚠️  MySQL doesn't seem to be running."
    echo "   Start it with: sudo systemctl start mysql"
    exit 1
fi

echo "Choose MySQL setup option:"
echo "1. Use existing MySQL root password"
echo "2. Create dedicated MySQL user (recommended)"
echo "3. Set root password for authentication"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        read -sp "Enter MySQL root password: " root_pass
        echo ""
        echo "Creating database and tables..."
        mysql -u root -p"$root_pass" < schema.sql 2>/dev/null || {
            echo "❌ Failed to create database. Check password."
            exit 1
        }
        echo "Inserting dummy data..."
        mysql -u root -p"$root_pass" < dummy_data.sql 2>/dev/null || {
            echo "❌ Failed to insert data."
            exit 1
        }
        echo ""
        echo "✅ Database setup complete!"
        echo ""
        echo "Add to your start.sh or export:"
        echo "  export MYSQL_USER='root'"
        echo "  export MYSQL_PASSWORD='$root_pass'"
        ;;
    2)
        echo ""
        read -sp "Enter MySQL root password (or press Enter for sudo): " root_pass
        echo ""
        if [ -z "$root_pass" ]; then
            echo "Using sudo to access MySQL..."
            sudo mysql < schema.sql
            sudo mysql <<EOF
CREATE USER IF NOT EXISTS 'outpass_user'@'localhost' IDENTIFIED BY 'outpass123';
GRANT ALL PRIVILEGES ON outpass_clean.* TO 'outpass_user'@'localhost';
FLUSH PRIVILEGES;
EOF
            sudo mysql < dummy_data.sql
        else
            mysql -u root -p"$root_pass" < schema.sql
            mysql -u root -p"$root_pass" <<EOF
CREATE USER IF NOT EXISTS 'outpass_user'@'localhost' IDENTIFIED BY 'outpass123';
GRANT ALL PRIVILEGES ON outpass_clean.* TO 'outpass_user'@'localhost';
FLUSH PRIVILEGES;
EOF
            mysql -u root -p"$root_pass" < dummy_data.sql
        fi
        echo ""
        echo "✅ Database setup complete!"
        echo ""
        echo "Add to your start.sh or export:"
        echo "  export MYSQL_USER='outpass_user'"
        echo "  export MYSQL_PASSWORD='outpass123'"
        ;;
    3)
        echo ""
        read -sp "Enter new MySQL root password: " new_pass
        echo ""
        read -sp "Confirm password: " confirm_pass
        echo ""
        if [ "$new_pass" != "$confirm_pass" ]; then
            echo "❌ Passwords don't match!"
            exit 1
        fi
        echo "Setting root password..."
        sudo mysql <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$new_pass';
FLUSH PRIVILEGES;
EOF
        echo "Creating database and tables..."
        mysql -u root -p"$new_pass" < schema.sql
        echo "Inserting dummy data..."
        mysql -u root -p"$new_pass" < dummy_data.sql
        echo ""
        echo "✅ Database setup complete!"
        echo ""
        echo "Add to your start.sh or export:"
        echo "  export MYSQL_USER='root'"
        echo "  export MYSQL_PASSWORD='$new_pass'"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Setup complete! Now run: ./start.sh"
echo "=========================================="
