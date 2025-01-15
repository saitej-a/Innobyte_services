import os
import sqlite3
from bcrypt import hashpw,gensalt,checkpw
import argparse
conn=sqlite3.connect('financial_database.db')
useridx=None
def create_user(username:str, password:str) -> str:
    hashed_pw=hashpw(password.encode(),gensalt())
    try:
        cursor=conn.cursor()
        cursor.execute('INSERT INTO users(username,password) VALUES(?,?)',(username,hashed_pw))
        conn.commit()
        return 'Registered User Successfully'
    except sqlite3.IntegrityError:
        return 'Use different Username or Log in with this Username'
    except Exception as e:
        return f'Something Went Wrong ({e})'
    finally:
        cursor.close()
def userLogin(username:str,password:str)->str:
    cursor=conn.cursor()
    cursor.execute('select password,userid from users where username=?',(username,))
    hashed_pw=cursor.fetchone()
    global useridx
    try:
        if not hashed_pw:
            return 'Incorrect Username'
        result=checkpw(password.encode(),hashed_pw[0])
        if result:
            with open('.session','w') as f:
                f.write(str(hashed_pw[1]))
            f.close()
            return 'Successful Login'
        else:
            return 'Incorrect Password or Username'
    finally:
        conn.close()
def userLogout()->None:
    try:
        os.remove('.session')
    except Exception:
        pass
def checkLimit(amount:float,category:str)->bool:
    global useridx
    cursor=conn.cursor()
    cursor.execute('select sum(amount) from budget where userid=? and category=?',(useridx,category))
    res=cursor.fetchone()
    if res[0]!=None:
        if amount<=res[0]:
            return (True,res[0])
        return (False,res[0])
    return (True,res[0])

def check_user(id:int)->bool:
    global useridx
    cursor=conn.cursor()
    cursor.execute('select userid from transactions where id=?',(id,))
    res=cursor.fetchone()
    if not res:
        print("Transaction record no longer availabe")
        return False
    if res[0]!=useridx:
        conn.close()
        print(f"You have no rights to update or delete this transaction (ID : {id})")
        return False
    return True
def load_user()->None:
    global useridx
    try:
        with open('.session','r') as f:
            useridx=int(f.read())
    except Exception:
        pass
    finally:
        try:
            f.close()
        except Exception:
            pass
def transact(amount:float,month:int,year:int,typeof:str,category:str):
    global useridx
    
    typeof=typeof.lower()
    category=category.lower()
    try:
        check,am=checkLimit(amount,category)
        if check and am!=None:
            cursor=conn.cursor()
            cursor.execute('insert into transactions(userid,amount,type,category,month,year) values(?,?,?,?,?,?) returning id',(useridx,amount,typeof,category,month,year))
            result=cursor.fetchone()
            t=am-amount
            cursor.execute('update budget set amount=? where userid=? and category=?',(t,useridx,category))
            conn.commit()
            print('Save this Transaction ID for later usages',result[0])
        elif check:
            cursor=conn.cursor()
            cursor.execute('insert into transactions(userid,amount,type,category,month,year) values(?,?,?,?,?,?) returning id',(useridx,amount,typeof,category,month,year))
            result=cursor.fetchone()
            conn.commit()
            print('Save this Transaction ID for later usages',result[0])
        else:
            inp=input(f'Limiting budget for {category} remaining Budget : {am}, Try updating (1) or deleting the existing budget (2) : ')
            if inp=='1':
                amounttemp=float(input('Budget Amount (floating) : '))
                updateBudget(amounttemp+am,category)
            elif inp=='2':
                deleteBudget(category)
            
    except Exception as e:
        print('Something went wrong',e)
    finally:
        conn.close()
    
    
def update_transact(id:int,item:str,val:str):
    res=check_user(id)
    if not res:
        return
    
    item=item.lower()
    if item=="amount":
        val=float(val)
    elif item=='month' or item=='year':
        val=int(val)
    try:
        cursor=conn.cursor()
        cursor.execute(f'update transactions set {item}=?  where id=?',(val,id))
        conn.commit()
    except Exception:
        print('Somethign went wrong')
    # cursor.execute('select * from transactions where id=?',(id,))
    # print(*cursor.fetchone(),sep=' | ')
    finally:
        conn.close()
    print("Updated Successfully")
def delete_transaction(id:int):
    res=check_user(id)
    if not res:
        return 
    try:
        cursor=conn.cursor()
        cursor.execute('delete from transactions where id=?',(id,))
        conn.commit()
        print('Transaction Successfully deleted')
    except Exception:
        print("Something went Wrong")
    finally:
        conn.close()
    
def finreports(month:int,year:int):
    global useridx
    cursor=conn.cursor()
    res=[]
    if not month and not year:
        cursor.execute('select type,sum(amount) from transactions where userid=? group by type',(useridx,))
        res=cursor.fetchall()
        conn.close()
    elif not month:
        cursor.execute('select type,sum(amount) from transactions where userid=? and year=? group by type',(useridx,year))
        res=cursor.fetchall()
        conn.close()
    elif month and year:
        cursor.execute('select type,sum(amount) from transactions where userid=? and month=? and year=? group by type',(useridx,month,year))
        res=cursor.fetchall()
        conn.close()
    else:
        print('Please specify year too')
        conn.close()
        return
    s=0
    for t,r in res:
        print(f'{t} : {r}')
        s+= r if t=='income' else -r
    print('savings :',s)
def setBudget(amount:float,category:str):
    global useridx
    category=category.lower()
    try:

        cursor=conn.cursor()
        cursor.execute('select id from budget where userid=? and category=?',(useridx,category))
        res=cursor.fetchone()
        if res:
            updateBudget(amount,category)
        else:
            cursor.execute('insert into budget(amount,category,userid) values (?,?,?) returning id',(amount,category,useridx))
            res=cursor.fetchone()
            conn.commit()
        print('Budget record ID :',res[0])
    except Exception:
        print('Something Went wrong')
    finally:
        conn.close()
def updateBudget(amount:float,category:str):
    category=category.lower()
    global useridx
    try:
        cursor=conn.cursor()
        cursor.execute('update budget set amount=? where userid=? and category=?',(amount,useridx,category))
        conn.commit()
        print('Updation Successful')
    except Exception:
        print('Something went wrong')
    
def deleteBudget(category:str):
    global useridx
    try:
        cursor=conn.cursor()
        cursor.execute('delete from budget where userid=? and category=?',(useridx,category))
        conn.commit()
    except Exception:
        print('Something went wrong')
def main():
    load_user()
    global useridx
    parser=argparse.ArgumentParser(description='Personal Finance CLI')
    subparser=parser.add_subparsers(dest='command',help='Description')
    createparser=subparser.add_parser('create_user',help='Create User')
    createparser.add_argument('username',type=str,help='Username')
    createparser.add_argument('password',type=str,help='Password')
    userlogin=subparser.add_parser('login',help="Login")
    userlogin.add_argument('username',type=str,help='Username')
    userlogin.add_argument('password',type=str,help='Password')
    transact_sub=subparser.add_parser('transact',help='Transact Money')
    transact_sub.add_argument('amount',type=float,help='Amount should in float')
    transact_sub.add_argument('type',type=str,help="Specify income or expense (case-sensitive)")
    transact_sub.add_argument('category',type=str,help='Food or Rent ... Etc')
    transact_sub.add_argument('month',type=int,help='Trasanction month (MM)')
    transact_sub.add_argument('year',type=int,help='Trasanction year (YY)')
    subparser.add_parser('logout',help='Logout')
    updateTr=subparser.add_parser('updatetr',help="Update Transactions")
    updateTr.add_argument('id',help='transaction ID',type=int)
    updateTr.add_argument('record',help='Column that you want to change',type=str)
    updateTr.add_argument('value',help='Value',type=str)
    delete_tr=subparser.add_parser('deletetr',help='Delete Transactions')
    delete_tr.add_argument('id',help='Transaction ID',type=int)
    finrep=subparser.add_parser('finrep',help='Financial reports')
    finrep.add_argument('--year',help='transaction year (MM)',type=int,default=0)
    finrep.add_argument('--month',help='transaction month (MM)',type=int,default=0)
    set_budget=subparser.add_parser('setbudget',help='Set budget for categories to get notfied')
    set_budget.add_argument('amount',type=float,help='Amount limit')
    set_budget.add_argument('category',help='Category(Food, Rent, Cab. etc)',type=str)

    args=parser.parse_args()
    if args.command=='create_user':
        print(create_user(args.username,args.password))
    elif args.command=='login':
        print(userLogin(args.username,args.password))
    elif args.command=='transact':
        if useridx:
            transact(amount=args.amount,typeof=args.type,category=args.category,month=args.month,year=args.year)
        else:
            print('log in to transact')
    elif args.command=='logout':
        if useridx:
            userLogout()
            print('Logged Out')
        else:
            print('No Login sessions were Detected')
    elif args.command=='updatetr':
        update_transact(args.id,args.record,args.value)
    elif args.command=='deletetr':
        delete_transaction(args.id)
    elif args.command=='finrep':
        finreports(month=args.month,year=args.year)
    elif args.command=='setbudget':
        setBudget(args.amount,args.category)
    else:
        parser.print_help()
if __name__=='__main__':
    main()
    
# cursor=conn.cursor()
# cursor.execute('create table transactions (id integer primary key autoincrement,userid integer not null,amount real not null, type text check (type in ("income","expense")),category char(50) not null, month integer not null,year integer not null,foreign key (userid) references users(userid)) ')
# cursor.execute('create table budget (id integer primary key autoincrement,userid integer not null,amount real not null,category char(50) not null,foreign key (userid) references users(userid))')
# cursor.execute('delete from budget')
# cursor.execute('delete from sqlite_sequence where name="budget"')
# print(cursor.fetchall())
# conn.commit()
# conn.close()
