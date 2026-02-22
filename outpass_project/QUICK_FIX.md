# 🔧 QUICK FIX: MySQL Authentication Error

## Problem
You're getting: `Access denied for user 'root'@'localhost'` (Error 1698)

## Solution (Choose ONE)

### ✅ Option 1: Run the Fix Script (EASIEST)

```bash
cd outpass_project
./fix_mysql.sh
```

This will:
- Create the MySQL user `outpass_user` with password `Outpass@1234`
- Create the database `outpass_clean`
- Import schema and dummy data
- Your `start.sh` already has the correct credentials!

Then restart your server:
```bash
./start.sh
```

---

### Option 2: Manual Fix (If script doesn't work)

**Step 1: Create MySQL user**
```bash
sudo mysql
```

Then run these SQL commands:
```sql
CREATE DATABASE IF NOT EXISTS outpass_clean;
CREATE USER IF NOT EXISTS 'outpass_user'@'localhost' IDENTIFIED BY 'Outpass@1234';
GRANT ALL PRIVILEGES ON outpass_clean.* TO 'outpass_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Step 2: Import schema and data**
```bash
cd outpass_project
mysql -u outpass_user -p'Outpass@1234' < schema.sql
mysql -u outpass_user -p'Outpass@1234' < dummy_data.sql
```

**Step 3: Restart server**
```bash
./start.sh
```

---

### Option 3: Use Root with Password (If you know root password)

If you know your MySQL root password:

```bash
export MYSQL_PASSWORD="your_root_password"
export MYSQL_USER="root"
```

Then restart server.

---

## Verify It Works

After fixing, try logging in:
- Tutor: http://127.0.0.1:8000/tutor_login.html
- Username: `tutor_cse`
- Password: `tutor123`

If you still get errors, check:
1. MySQL is running: `sudo systemctl status mysql`
2. Database exists: `mysql -u outpass_user -p'Outpass@1234' -e "SHOW DATABASES;"`
3. User exists: `mysql -u outpass_user -p'Outpass@1234' -e "SELECT user FROM mysql.user WHERE user='outpass_user';"`
