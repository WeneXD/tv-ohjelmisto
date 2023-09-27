import tclr

clr=tclr.clr()
if __name__=="__main__":
    print(f"{clr.warn}Run{clr.file} main.py{clr.warn} as main.\033[97m")
    quit()
import mysql.connector as mysqlc
from pydantic import BaseModel
import configparser as cparser
from os import path

cf=cparser.ConfigParser()

class Settings(BaseModel):  #Settings class for the database which to connect to.
    host:str="127.0.0.1"
    port:str="3306"
    user:str="user"
    pword:str="password"
    db:str="database"

    def load(self): #Use configparser to get the database's info from conf.ini
        if not path.exists("conf.ini"):     #Print error if file not found.
            print(f'{clr.file}conf.ini{clr.warn} not found. Most probably cannot connect to MySQL database with the default values.')
            return
        
        cf.read("conf.ini")
        self.host=str(cf.get("DB","Host"))  
        self.port=str(cf.get("DB","Port"))
        self.user=str(cf.get("DB","User"))
        self.pword=str(cf.get("DB","Password"))
        self.db=str(cf.get("DB","Database"))
        print(f"{clr.value}[{self.host}:{self.port}, {self.user}, {self.pword}, {self.db}]")

settings=Settings()
settings.load()

try:
    db=mysqlc.connect(  #Try to connect to the database
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.pword,
        database=settings.db
    )
except mysqlc.Error as e:   #Catch error and print it
    print(f"{clr.warn}[MySQL Error]\t{str(mysqlc.errors.Error(errno=e.errno))}, ({e.errno})\033[97m")
else:
    print(f"{clr.ok}Succesfully connected to database.\033[97m")

def get_users_OLD():    #Old deprecated way of getting users.
    out={}
    cur=db.cursor()
    cur.execute("select * from käyttäjät")
    cur.fetchall()
    print(cur.rowcount)
    for x in cur:
        print(x)
        out[x[0]]=list(x)
        out[x[0]].pop(0)
    cur.close()
    print(out)
    return out

def get_users():
    out={"out":False}
    users=[]
    cur=db.cursor(buffered=True)
    query="select * from käyttäjät"
    
    cur.execute(query)

    for x in cur:
        #print(x)
        us=[x[0],x[1],x[2],x[4]]    #ID, forename, surname, level, (3=password)
        users.append(us)
    
    out={"out":True,"users":users}

    cur.close()

    return out

def get_user(uid):
    out={}
    cur=db.cursor()
    query="select * from käyttäjät where id=%s"
    cur.execute(query,(uid,))
    for x in cur:
        out[x["ID"]]=x
    cur.close()
    return out

def log_in(ID,pword):
    out={"out":False}
    cur=db.cursor(buffered=True)
    query="select salasana from käyttäjät where id=%s"
    cur.execute(query,(ID,))    #Get the password for user with the ID.
    
    for x in cur:
        if x[0]==pword: #Check if given password is correct.
            out={"out":True}
            break
    
    if cur.rowcount==0: #If the rowcount is 0 it means no user with the ID was found.
        out={"out":False,"err":"Invalid ID"}
        return out

    if not out["out"]:  #Password wasn't correct
        out={"out":False,"err":"Invalid password"}
        return out

    cur.close()     #Close the cursor
    new_cur=db.cursor(buffered=True) #Create new cursor

    query="select etunimi, sukunimi, rooli from käyttäjät where id=%s"
    new_cur.execute(query,(ID,))
    
    for x in new_cur:
        out={"out":True,"etunimi":x[0],"sukunimi":x[1], "lvl":x[2]}

    new_cur.close()

    return out

def get_employees():
    out={"out":False}
    employees=[]
    cur=db.cursor(buffered=True)
    query="select id, etunimi, sukunimi from käyttäjät where rooli=0"
    
    cur.execute(query)

    for x in cur:
        emp=[x[0],x[1],x[2]]
        employees.append(emp)
    
    out={"out":True,"employees":employees}

    cur.close()

    return out

def get_shifts(_ID):
    out={"out":False}
    ID=str(_ID)
    shifts=[]
    cur=db.cursor(buffered=True)
        #tv=työvuoro
    query="select id, tv_salku, tv_sloppu, tv_alku, tv_loppu, työtehtävä, pvmäärä, ylityöt, kommentti from työvuoro where k_id=%s"

    cur.execute(query,(ID,))

    for x in cur:   #Loop through the cursor.
        shift=[]    #Create a list for a shift.
        for y in x:     #Loop through cursor's list of the shift.
            shift.append(y) #Fill the shift list with the shift's info.
        #print(shift)
        shifts.append(shift)    #Append the current shift list to the shifts list.

    out={"out":True,"shifts":shifts}
    
    cur.close()

    return out

def log_shift(_ID,_K_ID,aloitus,lopetus,kommentti):
        #Self_explanatory function
    ID=str(_ID)
    K_ID=str(_K_ID)
    cur=db.cursor(buffered=True)
    query="update työvuoro set tv_alku=%s, tv_loppu=%s, kommentti=%s where id=%s and k_id=%s"

    cur.execute(query,(aloitus,lopetus,kommentti,ID,K_ID,))

    db.commit()

    out={"out":True}
    
    cur.close()

    return out

def add_shift(_K_ID,s_aloitus,s_lopetus,teht,pv):
    out={"out":False}
    K_ID=str(_K_ID)
    cur=db.cursor(buffered=True)

    query="select rooli from käyttäjät where id=%s"

    cur.execute(query,(K_ID,))

    for x in cur:
        if x[0]==1:
            out={"out":False,"err":"Cannot give shifts to employers"}
            return out

    if cur.rowcount==0:
        out={"out":False,"err":"Invalid ID"}
        return out
    
    cur.close()

    new_cur=db.cursor(buffered=True)

    
    query="insert into työvuoro values (default, %s, %s, %s, null, null, %s, %s, null, null)"

    try:
        new_cur.execute(query,(K_ID,s_aloitus,s_lopetus,teht,pv,))
    except mysqlc.Error as e:
        return {"out":False,"err":f"[SQL ERROR] {e}"}
    else:
        db.commit()
        
        new_cur.close()

        out={"out":True}

        return out

def add_user(name,pword,lvl):
    out={"out":False}
    if lvl!=0 and lvl!=1:
        out={"out":False,"err":"Invalid user role"}
    
    cur=db.cursor(buffered=True)

    query="insert into käyttäjät values (default, %s, %s, %s, %s)"

    cur.execute(query,(name[0],name[1],pword,int(lvl)))
    cur.close()

    db.commit()

    out={"out":True}
    return out

def delete_user(ID):
    out={"out":False}
    
    cur=db.cursor(buffered=True)

    query="delete from käyttäjät where id=%s"

    cur.execute(query,(ID,))
    cur.close()

    new_cur=db.cursor(buffered=True)

    query="delete from työvuoro where k_id=%s"

    new_cur.execute(query,(ID,))
    new_cur.close()

    db.commit()

    out={"out":True}
    return out

print("\033[97m",end="")