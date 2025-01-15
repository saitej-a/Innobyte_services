import pandas as pd
import os
import sqlite3
from bcrypt import hashpw, gensalt, checkpw
import argparse

# Establish a connection to the SQLite database
conn = sqlite3.connect('financial_database.db')
useridx = None  # Global variable to store the current user's ID

def create_user(username: str, password: str) -> str:
    """
    Create a new user with a hashed password.
    
    Args:
        username (str): The username for the new user.
        password (str): The password for the new user.
    
    Returns:
        str: A message indicating the result of the operation.
    """
    hashed_pw = hashpw(password.encode(), gensalt())  # Hash the password
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users(username,password) VALUES(?,?)', (username, hashed_pw))
        conn.commit()
        return 'Registered User Successfully'
    except sqlite3.IntegrityError:
        return 'Use different Username or Log in with this Username'
    except Exception as e:
        return f'Something Went Wrong ({e})'
    finally:
        cursor.close()

def userLogin(username: str, password: str) -> str:
    """
    Log in a user by verifying the username and password.
    
    Args:
        username (str): The username of the user.
        password (str): The password of the user.
    
    Returns:
        str: A message indicating the result of the login attempt.
    """
    cursor = conn.cursor()
    cursor.execute('select password,userid from users where username=?', (username,))
    hashed_pw = cursor.fetchone()
    global useridx
    try:
        if not hashed_pw:
            return 'Incorrect Username'
        result = checkpw(password.encode(), hashed_pw[0])  # Check the hashed password
        if result:
            with open('.session', 'w') as f:
                f.write(str(hashed_pw[1]))  # Store user ID in a session file
            return 'Successful Login'
        else:
            return 'Incorrect Password or Username'
    finally:
        conn.close()

def userLogout() -> None:
    """
    Log out the current user by removing the session file.
    """
    try:
        os.remove('.session')  # Remove the session file
    except Exception:
        pass

def checkLimit(amount: float, category: str) -> bool:
    """
    Check if a transaction amount exceeds the budget limit for a given category.
    
    Args:
        amount (float): The amount to check.
        category (str): The category of the transaction.
    
    Returns:
        bool: True if the amount is within the limit, False otherwise.
    """
    global useridx
    cursor = conn.cursor()
    cursor.execute('select sum(amount) from budget where userid=? and category=?', (useridx, category))
    res = cursor.fetchone()
    if res[0] is not None:
        if amount <= res[0]:
            return (True, res[0])  # Amount is within the limit
        return (False, res[0])  # Amount exceeds the limit
    return (True, res[0])  # No budget set for the category

def check_user(id: int) -> bool:
    """
    Check if the user has rights to update or delete a transaction.
    
    Args:
        id (int): The transaction ID to check.
    
    Returns:
        bool: True if the user has rights, False otherwise.
    """
    global useridx
    cursor = conn.cursor()
    cursor.execute('select userid from transactions where id=?', (id,))
    res = cursor.fetchone()
    if not res:
        print("Transaction record no longer available")
        return False
    if res[0] != useridx:
        conn.close()
        print(f"You have no rights to update or delete this transaction (ID : {id})")
        return False
    return True

def load_user() -> None:
    """
    Load the current user's ID from the session file.
    """
    global useridx
    try:
        with open('.session', 'r') as f:
            useridx = int(f.read())  # Read user ID from session file
    except Exception:
        pass
    finally:
        try:
            f.close()
        except Exception:
            pass

def transact(amount: float, month: int, year: int, typeof: str, category: str):
    """
    Record a transaction and update the budget accordingly.
    
    Args:
        amount (float): The amount of the transaction.
        month (int): The month of the transaction.
        year (int): The year of the transaction.
        typeof (str): The type of transaction ('income' or 'expense').
 category (str): The category of the transaction.
    """
    global useridx
    
    typeof = typeof.lower()
    category = category.lower()
    try:
        check, am = checkLimit(amount, category)  # Check if the transaction amount is within the budget
        if check and am is not None:
            cursor = conn.cursor()
            cursor.execute('insert into transactions(userid,amount,type,category,month,year) values(?,?,?,?,?,?) returning id',
                           (useridx, amount, typeof, category, month, year))
            result = cursor.fetchone()
            t = am - amount  # Update remaining budget
            cursor.execute('update budget set amount=? where userid=? and category=?', (t, useridx, category))
            conn.commit()
            print('Save this Transaction ID for later usages', result[0])
        elif check:
            cursor = conn.cursor()
            cursor.execute('insert into transactions(userid,amount,type,category,month,year) values(?,?,?,?,?,?) returning id',
                           (useridx, amount, typeof, category, month, year))
            result = cursor.fetchone()
            conn.commit()
            print('Save this Transaction ID for later usages', result[0])
        else:
            inp = input(f'Limiting budget for {category} remaining Budget : {am}, Try updating (1) or deleting the existing budget (2) : ')
            if inp == '1':
                amounttemp = float(input('Budget Amount (floating) : '))
                updateBudget(amounttemp + am, category)  # Update budget if user chooses to do so
            elif inp == '2':
                deleteBudget(category)  # Delete budget if user chooses to do so
            
    except Exception as e:
        print('Something went wrong', e)
    finally:
        conn.close()

def update_transact(id: int, item: str, val: str):
    """
    Update a specific transaction based on the provided ID and field.
    
    Args:
        id (int): The transaction ID to update.
        item (str): The field to update (e.g., 'amount', 'month', 'year').
        val (str): The new value for the specified field.
    """
    res = check_user(id)  # Check if the user has rights to update the transaction
    if not res:
        return
    
    item = item.lower()
    if item == "amount":
        val = float(val)  # Convert value to float if updating amount
    elif item == 'month' or item == 'year':
        val = int(val)  # Convert value to int if updating month or year
    try:
        cursor = conn.cursor()
        cursor.execute(f'update transactions set {item}=? where id=?', (val, id))
        conn.commit()
    except Exception:
        print('Something went wrong')
    finally:
        conn.close()
    print("Updated Successfully")

def delete_transaction(id: int):
    """
    Delete a transaction based on the provided ID.
    
    Args:
        id (int): The transaction ID to delete.
    """
    res = check_user(id)  # Check if the user has rights to delete the transaction
    if not res:
        return 
    try:
        cursor = conn.cursor()
        cursor.execute('delete from transactions where id=?', (id,))
        conn.commit()
        print('Transaction Successfully deleted')
    except Exception:
        print("Something went Wrong")
    finally:
        conn.close()

def finreports(month: int, year: int):
    """
    Generate financial reports based on the specified month and year.
    
    Args:
        month (int): The month for the report.
        year (int): The year for the report.
    """
    global useridx
    cursor = conn.cursor()
    res = []
    if not month and not year:
        cursor.execute('select type,sum(amount) from transactions where userid=? group by type', (useridx,))
        res = cursor.fetchall()
        conn.close()
    elif not month:
        cursor.execute('select type,sum(amount) from transactions where userid=? and year=? group by type', (useridx, year))
        res = cursor.fetchall()
        conn.close()
    elif month and year:
        cursor.execute('select type,sum(amount) from transactions where userid=? and month=? and year=? group by type', (useridx, month, year))
        res = cursor.fetchall()
        conn.close()
    else:
        print('Please specify year too')
        conn.close()
        return
    s = 0
    for t, r in res:
        print(f'{t} : {r}')
        s += r if t == 'income' else -r  # Calculate savings
    print('savings :', s)

def setBudget(amount: float, category: str):
    """
    Set a budget for a specific category.
    
    Args:
        amount (float): The budget amount to set.
        category (str): The category for which the budget is being set.
    """
    global useridx
    category = category.lower()
    try:
        cursor = conn.cursor()
        cursor.execute('select id from budget where userid=? and category=?', (useridx, category))
        res = cursor.fetchone()
        if res:
            updateBudget(amount, category)  # Update existing budget if it exists
        else:
            cursor.execute('insert into budget(amount,category,userid) values (?,?,?) returning id', (amount, category, useridx))
            res = cursor.fetchone()
            conn.commit()
        print('Budget record ID :', res[0])
    except Exception:
        print('Something Went wrong')
    finally:
        conn.close()

def updateBudget(amount: float, category: str):
    """
    Update the budget amount for a specific category.
    
    Args:
        amount (float): The new budget amount.
        category (str): The category for which the budget is being updated.
    """
    category = category.lower()
    global useridx
    try:
        cursor = conn.cursor()
        cursor.execute('update budget set amount=? where userid=? and category=?', (amount, useridx, category))
        conn.commit()
        print('Updation Successful')
    except Exception:
        print('Something went wrong')

def deleteBudget(category: str):
    """
    Delete the budget for a specific category.
    
    Args:
        category (str): The category for which the budget is being deleted.
    """
    global useridx
    try:
        cursor = conn.cursor()
        cursor.execute('delete from budget where userid=? and category=?', (useridx, category))
        conn.commit()
    except Exception:
        print('Something went wrong')

def backup(type: str):
    """
    Create a backup of the specified table (users or transactions) to a CSV file.
    
    Args:
        type (str): The name of the table to back up.
    """
    type = type.lower()
    try:
        table = pd.read_sql_query(f'select * from {type}', conn)  # Read the table into a DataFrame
        table.to_csv(f'{type}backup.csv', index=False)  # Save the DataFrame to a CSV file
        print('Backup completed Successfully')
    except Exception:
        print('Something Went Wrong (check the spelling (transactions or users)) ')
    finally:
        conn.close()

def restore(type1: str, path: str):
    """
    Restore records from a CSV file into the specified table (users or transactions).
    
    Args:
        type1 (str): The name of the table to restore data into.
        path (str): The path to the CSV file containing the data.
    """
    type1 = type1.lower()
    try:
        table = pd.read_csv(path)  # Read the CSV file into a DataFrame
        table.to_sql(f'{type1}', conn, if_exists='append', index=False)  # Append the DataFrame to the specified table
        print('Restoration Completed Successfully')
    except Exception as e:
        print('Something went wrong', e)
    finally:
        conn.close()

def main():
    """
    Main function to handle command-line interface for the personal finance application.
    """
    load_user()  # Load the current user from the session file
    global useridx
    parser = argparse.ArgumentParser(description='Personal Finance CLI')
    subparser = parser.add_subparsers(dest='command', help='Description')
    
    # Subparser for creating a user
    createparser = subparser.add_parser('create_user', help='Create User')
    createparser.add_argument('username', type=str, help='Username')
    createparser.add_argument('password', type=str, help='Password')
    
    # Subparser for user login
    userlogin = subparser.add_parser('login', help="Login")
    userlogin.add_argument('username', type=str, help='Username')
    userlogin.add_argument('password', type=str, help='Password')
    
    # Subparser for transactions
    transact_sub = subparser.add_parser('transact', help='Transact Money')
    transact_sub.add_argument('amount', type=float, help='Amount should in float')
    transact_sub.add_argument('type', type=str, help="Specify income or expense (case-sensitive)")
    transact_sub.add_argument('category', type=str, help='Food or Rent ... Etc')
    transact_sub.add_argument('month', type=int, help='Transaction month (MM)')
    transact_sub.add_argument('year', type=int, help='Transaction year (YY)')
    
    # Subparser for user logout
    subparser.add_parser('logout', help='Logout')
    
    # Subparser for updating transactions
    updateTr = subparser.add_parser('updatetr', help="Update Transactions")
    updateTr.add_argument('id', help='Transaction ID', type=int)
    updateTr.add_argument('record', help='Column that you want to change', type=str)
    updateTr.add_argument('value', help='Value', type=str)
    
    # Subparser for deleting transactions
    delete_tr = subparser.add_parser('deletetr', help='Delete Transactions')
    delete_tr.add_argument('id', help='Transaction ID', type=int)
    
    # Subparser for generating financial reports
    finrep = subparser.add_parser('finrep', help='Financial reports')
    finrep.add_argument('--year', help='Transaction year (YYYY)', type=int, default=0)
    finrep.add_argument('--month', help='Transaction month (MM)', type=int, default=0)
    
    # Subparser for setting budgets
    set_budget = subparser.add_parser('setbudget', help='Set budget for categories to get notified')
    set_budget.add_argument('amount', type=float, help='Amount limit')
    set_budget.add_argument('category', help='Category (Food, Rent, Cab, etc.)', type=str)
    
    # Subparser for backing up data
    backup_command = subparser.add_parser('backup', help='Backups transactions and users')
    backup_command.add_argument('table_name', help='Users or transactions', type=str)
    
    # Subparser for restoring data
    restore_command = subparser.add_parser('restore', help='Restore records by uploading backup file')
    restore_command.add_argument('table_name', help='Table name (users or transactions)', type=str)
    restore_command.add_argument('path', help='CSV file path (drag and drop here)', type=str)
    
    args = parser.parse_args()  # Parse command-line arguments
    
    # Execute commands based on user input
    if args.command == 'create_user':
        print(create_user(args.username, args.password))
    elif args.command == 'login':
        print(userLogin(args.username, args.password))
    elif args.command == 'transact':
        if useridx:
            transact(amount=args.amount, typeof=args.type, category=args.category, month=args.month, year=args.year)
        else:
            print('Log in to transact')
    elif args.command == 'logout':
        if useridx:
            userLogout()
            print('Logged Out')
        else:
            print('No Login sessions were Detected')
    elif args.command == 'updatetr':
        update_transact(args.id, args.record, args.value)
    elif args.command == 'deletetr':
        delete_transaction(args.id)
    elif args.command == 'finrep':
        finreports(month=args.month, year=args.year)
    elif args.command == 'setbudget':
        setBudget(args.amount, args.category)
    elif args.command == 'backup':
        backup(args.table_name)
    elif args.command == 'restore':
        restore(args.table_name, args.path)
    else:
        parser.print_help()  # Show help if command is not recognized

if __name__ == '__main__':
    main()  # Run the main function when the script is executed