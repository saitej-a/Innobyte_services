
---

# **Personal Finance Management System Documentation**

This script provides a command-line interface (CLI) to manage personal finances, including user management, transactions, budgeting, and reporting.

## **Table of Contents**
1. [Dependencies and Setup](#dependencies-and-setup)
2. [Database and Global Variables](#database-and-global-variables)
3. [Functions](#functions)
    - [User Management](#user-management)
    - [Session Management](#session-management)
    - [Transactions](#transactions)
    - [Budgeting](#budgeting)
    - [Backup and Restore](#backup-and-restore)
4. [CLI Commands](#cli-commands)

---

## **Dependencies and Setup**
The following libraries are required:
- `pandas` - For data manipulation and backups.
- `os` - For file operations.
- `sqlite3` - To interact with the SQLite database.
- `bcrypt` - For password hashing and verification.
- `argparse` - For CLI argument parsing.

Make sure to install these libraries using `pip` if they are not already installed.

```bash
pip install pandas bcrypt
```

---

## **Database and Global Variables**

### Database
The SQLite database (`financial_database.db`) stores user, transaction, and budget information. Key tables:
- `users`: Contains `userid`, `username`, and hashed `password`.
- `transactions`: Stores `userid`, `amount`, `type`, `category`, `month`, and `year`.
- `budget`: Maintains `userid`, `amount`, and `category`.

### Global Variables
- `conn`: A connection object for the SQLite database.
- `useridx`: Stores the currently logged-in user's ID.

---

## **Functions**

### **User Management**

#### `create_user(username: str, password: str) -> str`
Creates a new user with a hashed password.
- **Args**:
  - `username` (str): Desired username.
  - `password` (str): Plain-text password.
- **Returns**: Success or error message.

#### `userLogin(username: str, password: str) -> str`
Authenticates a user and starts a session.
- **Args**:
  - `username` (str): Username.
  - `password` (str): Plain-text password.
- **Returns**: Login success or failure message.

---

### **Session Management**

#### `load_user() -> None`
Loads the current user's session ID from the `.session` file.

#### `userLogout() -> None`
Logs out the user by deleting the `.session` file.

---

### **Transactions**

#### `transact(amount: float, month: int, year: int, typeof: str, category: str)`
Records a financial transaction.
- **Args**:
  - `amount` (float): Transaction amount.
  - `month` (int): Transaction month.
  - `year` (int): Transaction year.
  - `typeof` (str): `income` or `expense`.
  - `category` (str): Transaction category.

#### `update_transact(id: int, item: str, val: str)`
Updates a specific field of a transaction.
- **Args**:
  - `id` (int): Transaction ID.
  - `item` (str): Field to update (`amount`, `month`, `year`, etc.).
  - `val` (str): New value.

#### `delete_transaction(id: int)`
Deletes a transaction.
- **Args**:
  - `id` (int): Transaction ID.

#### `finreports(month: int, year: int)`
Generates financial reports for a specified month and year.
- **Args**:
  - `month` (int): Month for the report (optional).
  - `year` (int): Year for the report (optional).

---

### **Budgeting**

#### `setBudget(amount: float, category: str)`
Sets a budget for a specific category.
- **Args**:
  - `amount` (float): Budget amount.
  - `category` (str): Budget category.

#### `updateBudget(amount: float, category: str)`
Updates the budget for a specific category.
- **Args**:
  - `amount` (float): New budget amount.
  - `category` (str): Budget category.

#### `deleteBudget(category: str)`
Deletes a budget for a specific category.
- **Args**:
  - `category` (str): Budget category.

#### `checkLimit(amount: float, category: str) -> bool`
Checks if a transaction amount exceeds the category budget.
- **Args**:
  - `amount` (float): Transaction amount.
  - `category` (str): Transaction category.
- **Returns**: Whether the transaction is within budget.

---

### **Backup and Restore**

#### `backup(type: str)`
Creates a backup of a table (`users` or `transactions`) in CSV format.
- **Args**:
  - `type` (str): Table name to back up.

#### `restore(type1: str, path: str)`
Restores data from a CSV file to a table (`users` or `transactions`).
- **Args**:
  - `type1` (str): Table name.
  - `path` (str): Path to the CSV file.

---

## **CLI Commands**

### Overview
The CLI commands are implemented using the `argparse` module. Use `python script.py --help` to view available commands.

### Commands and Arguments
- `create_user <username> <password>`: Registers a new user.
- `login <username> <password>`: Logs in a user.
- `logout`: Logs out the current user.
- `transact <amount> <type> <category> <month> <year>`: Records a transaction.
- `updatetr <id> <record> <value>`: Updates a transaction.
- `deletetr <id>`: Deletes a transaction.
- `finrep [--month <MM>] [--year <YYYY>]`: Generates financial reports.
- `setbudget <amount> <category>`: Sets a budget.
- `backup <table_name>`: Backs up a table to a CSV file.
- `restore <table_name> <path>`: Restores a table from a CSV file.

---

## **Examples**

1. **Create a User**:
   ```bash
   python script.py create_user john_doe password123
   ```

2. **Log in**:
   ```bash
   python script.py login john_doe password123
   ```

3. **Record a Transaction**:
   ```bash
   python script.py transact 500 expense groceries 12 2023
   ```

4. **Set a Budget**:
   ```bash
   python script.py setbudget 1000 groceries
   ```

5. **Generate a Report**:
   ```bash
   python script.py finrep --month 12 --year 2023
   ```

6. **Backup Data**:
   ```bash
   python script.py backup transactions
   ```

---
