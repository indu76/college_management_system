#!/bin/bash

# Outpass Management System - Startup Script
# Sets environment variables and starts the FastAPI server

export GMAIL_USER="indhu9186@gmail.com"
export GMAIL_APP_PASSWORD="kmetedggwvfwegep"

# MySQL configuration - CHANGE THE PASSWORD!
export MYSQL_HOST="localhost"
export MYSQL_USER="outpass_user"
export MYSQL_PASSWORD="Outpass@1234"
export MYSQL_DATABASE="outpass_clean"

# If MySQL root uses auth_socket, create a user instead:
# sudo mysql -e "CREATE USER 'outpass_user'@'localhost' IDENTIFIED BY 'outpass123';"
# sudo mysql -e "GRANT ALL ON outpass_clean.* TO 'outpass_user'@'localhost';"
# Then use: export MYSQL_USER="outpass_user"
#          export MYSQL_PASSWORD="outpass123"

echo "Starting Outpass Management System..."
echo "Gmail User: $GMAIL_USER"
echo "MySQL Database: $MYSQL_DATABASE"
echo ""
echo "Server will start at: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop"
echo ""

uvicorn main:app --reload
