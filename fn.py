import tclr #Custom python file for colors.
clr=tclr.clr()  #Color class
if __name__=="__main__":
    print(f"{clr.warn}Run{clr.file} main.py{clr.warn} as main.\033[97m")
    quit()
from pydantic import BaseModel
import time as t
import hashlib as hlib
import base64
import random as rd
import configparser as cparser
from os import path
import threading as th
import re
import sql

cf = cparser.ConfigParser()

if path.exists("conf.ini"):
    cf.read("conf.ini")
else:
    print(f"{clr.warn}FILE {clr.file}conf.ini {clr.warn}NOT FOUND.")

users={}

def b64(x,y):
    y=str(y)
    if x=="enc": mBytes=y.encode("utf-8"); b64Bytes=base64.b64encode(mBytes); return b64Bytes.decode("utf-8")
    elif x=="dec": b64Bytes=y.encode("utf-8"); mBytes=base64.b64decode(b64Bytes); return mBytes.decode("utf-8")

def dict_decode_strings(d):
    new_dict={}
    for k,v in d.items():
        if v!=None:
            new_dict[k]=b64("dec",str(v))
        elif type(v)==list:
            new_list=[]
            for x in v:
                _x=b64("dec",str(x))
                new_list.append(_x)
        else:
            new_dict[k]=-1
    return new_dict

class Settings(BaseModel):
    LogLevelList:list[str]=["critical","debug"]
    AutoLogOut:bool=True    #Automatically log out user after a prolonged time of inactivity.
    LogOutTime:float=10   #How long the user can remain inactive for before getting logged out.
    MultiLogin:bool=False   #Allow multiple instances of one user logged in.
    LogLevel:int=1
    ADMIN:dict={"ID":"ADMIN","pword":".ADMIN"}


    def load(self):
        if cf.has_section("SERVER"):
            self.AutoLogOut=cf.getboolean("SERVER","AutoLogOut")
            self.LogOutTime=float(cf.get("SERVER","LogOutTime"))
            self.MultiLogin=cf.getboolean("SERVER","MultiLogin")
            self.LogLevel=int(cf.get("SERVER","LogLevel"))
        else:
            print(f"{clr.warn}NO{clr.value} [SERVER]{clr.warn} SECTION IN{clr.file} conf.ini{clr.warn} FOUND. ASSUMING DEFAULT VALUES.\033[97m")
        if cf.has_section("ADMIN"):
            self.ADMIN["ID"]=cf.get("ADMIN","ID")
            self.ADMIN["pword"]=cf.get("ADMIN","Password")
        else:
            print(f"{clr.warn}NO{clr.value} [ADMIN]{clr.warn} SECTION IN{clr.file} conf.ini{clr.warn} FOUND. ASSUMING DEFAULT CREDENTIALS.\nRECOMMENDED TO ADD{clr.value} [ADMIN]{clr.warn} SECTION TO{clr.file} conf.ini{clr.warn} WITH VALUES{clr.value} ID{clr.warn} AND{clr.value} pword{clr.warn} (CASE SENSITIVE).")
        print(f"{clr.ok}Server settings loaded.\033[97m")

settings=Settings()
settings.load()

class User(BaseModel):
    ID:int  #User's ID
    name:str    #User's name
    pword:str   #User's password (Hopefully hashed)
    lvl:int   #User's control level (Employee/Employer/Admin, 0/1/2)
    lastAct:float=t.time()  #Last time user was active (Unix time)

    def uAct(self): #Update user's last time of activity.
        self.lastAct=t.time()

stop_inact_thread=th.Event()

def inactive_logout():
    while not stop_inact_thread.is_set():   #Start the thread if not already started.
        t.sleep(30)
        if stop_inact_thread.is_set():
            break
        delList=[]
        print(f"{clr.ok}Checking for inactive users.")
        for tk, us in users.items():
            if (us.lastAct+settings.LogOutTime*60)-t.time()<0: #LastActivity + Allowed inactivity time - Current Time
                delList.append(tk)
        print(f"{clr.ok}Inactive users found:{clr.value} {len(delList)}")
        for tk in delList:
            del users[tk]
        if len(users)==0:
            stop_inact_thread.set()
        
    stop_inact_thread.clear()

inactivity_thread=th.Thread(target=inactive_logout)

    #Deprecated old log-in
"""
def log_in(_ID,pword):
    ID=int(_ID)
    global inactivity_thread
    cnt=1
    delList=[]
    if not settings.MultiLogin: #Checks if the server allows multiple instances of one user online.
        for tk, us in users.items():    #Checks if someone is already locked in the account.
            if us.ID==ID:
                delList.append(tk)   #Adds user instance to list for deletion.
        for tk in delList:  
            del users[tk]   #Delete the users in the deletion list

    token=generate_token(ID)
    while token in users:   #Generate unique session token
        generate_token(ID)

    newUser=User(ID=ID,name="Janipetteri",pword=pword,lvl=1)
    users[token]=newUser
    if not inactivity_thread.is_alive() and settings.AutoLogOut:    #Start inactivity check thread if not already on
        try:    #Try is used in case thread has already been started once and needs to be reset.
            inactivity_thread.start()
        except RuntimeError:
            inactivity_thread=th.Thread(target=inactive_logout)
            inactivity_thread.start()

    return {"out":True,"token":token}
"""
def log_in(_ID,pword):  #SQL-Based log-in
    if _ID[:1]=="@":    #If first symbol of user ID is @, use the admin credentials.
        if _ID[1:]==settings.ADMIN["ID"] and pword==settings.ADMIN["pword"]:
            ID=-1
            out={"etunimi":"ADMIN","sukunimi":"","pword":pword,"lvl":2}
        else:
            out={"out":False,"err":"Invalid ID or password."}
            return out
    else:               #Otherwise try logging into a user in the database.
        x=re.sub("[^0-9]","",_ID)
        if len(_ID)!=len(x):    #Check if given ID only contains numbers and if it does then return.
            out={"out":False,"err":"Invalid user ID"}
            return out

        ID=int(_ID)
        global inactivity_thread
        cnt=1
        delList=[]

        out=sql.log_in(ID,pword)
        if not out["out"]:
            return out

        if not settings.MultiLogin: #Checks in the server allows multiple instances of one user online.
            for tk, us in users.items():    #Checks if someone is already logged into the account.
                if us.ID==ID:
                    delList.append(tk)  #Adds user instance to list for deletion.
            for tk in delList:
                del users[tk]   #Delete the users in the deletion list

    token=generate_token(_ID)
    while token in users:   #Generate an unique session token for the user.
        generate_token(_ID)  

    newUser=User(ID=ID,name=f'{out["etunimi"]} {out["sukunimi"]}',pword=pword,lvl=out["lvl"])
    users[token]=newUser
    if not inactivity_thread.is_alive() and settings.AutoLogOut:    #Start inactivity check thread if not already on
        try:    #Try is used in case thread has already been started once and needs to be reset.
            inactivity_thread.start()
        except RuntimeError:
            inactivity_thread=th.Thread(target=inactive_logout)
            inactivity_thread.start()

    return {"out":True,"token":token,"lvl":out["lvl"],"name0":out['etunimi'],"name1":out['sukunimi']}


def log_out(token,pword):
    if token not in users: return {"out":False,"err":"User invalid"}    #User not found in the users dict.
    if users[token].pword!=pword: return {"out":False,"err":"Password invalid"} #User password is incorrect.
    
    del users[token]
    if len(users)==0:   #If the amount of users logged in is 0, inactivity_thread gets stopped.
        stop_inact_thread.set()
    return {"out":True}

def get_users(token,pword):
    _x=validate_user(token,pword,1)
    if not _x["out"]:
        return _x

    userlist=[] #Create list for users
    _users=list(users.values())
    for x in _users:    #Loop through users and append them to the list.
        userlist.append(x.name)

    return userlist #Return userlist

def sql_get_users(token,pword):
    _x=validate_user(token,pword,2)
    if not _x["out"]:
        return _x
    
    out=sql.get_users()
    return out

    #DEPRECATED FUNCTION
def sql_get_user(token,pword,uid):
    _x=validate_user(token,pword,1)
    if not _x["out"]:
        return _x

    out=sql.get_user(uid)
    if len(out)==0: #No user found if dict length is 0.
        out={"out":False,"err":"Invalid user ID"}
    return out


def sql_get_employees(token,pword):
    _x=validate_user(token,pword,1)
    if not _x["out"]:
        return _x

    out=sql.get_employees()
    return out

def sql_get_shifts(token,pword,ID):
    if token not in users: return {"out":False,"err":"User invalid"}

    #print(ID)

    if ID<0:
        ID=None

    if ID!=None:
        _x=validate_user(token,pword,1)
    else:
        _x=validate_user(token,pword,0)

    if not _x["out"]:
        return _x

    if ID==None:    #If no ID then get the user's ID.
        ID=users[token].ID

    out=sql.get_shifts(ID)
    return out

def sql_log_shift(token,pword,ID,aloitus,lopetus,kommentti):
    _x=validate_user(token,pword,0)

    if not _x["out"]:
        return _x

    inv_time={"out":False,"err":"Invalid time"}

    for x in [aloitus,lopetus]: #Check if the time is in the correct format (HH:MM)
        if len(x)<5:
            return inv_time
        y=re.sub("[^0-9]","",x[:2])+re.sub("[^:]","",x[2:3])+re.sub("[^0-9]","",x[3:5])
        if len(x)!=len(y):
            return inv_time
        if int(x[:2])>23:
            return inv_time
        if int(x[:3:5])>59:
            return inv_time
        x=y[:5]

    if len(kommentti)>200:  #Don't let the comment be too long.
        return {"out":False,"err":"Comment too long"}

    K_ID=users[token].ID

    out=sql.log_shift(ID,K_ID,aloitus,lopetus,kommentti)
    return out

def sql_add_shift(token,pword,K_ID,s_aloitus,s_lopetus,teht,pv):
    _x=validate_user(token,pword,1)

    if not _x["out"]:
        return _x
    
    inv_time={"out":False,"err":"Invalid time"}

    for x in [s_aloitus,s_lopetus]: #Check if time is in the correct format (HH:MM)
        if len(x)<5:
            return inv_time
        y=re.sub("[^0-9]","",x[:2])+re.sub("[^:]","",x[2:3])+re.sub("[^0-9]","",x[3:5])
        if len(x)!=len(y):
            return inv_time
        if int(x[:2])>23:
            return inv_time
        if int(x[3:5])>59:
            return inv_time
        x=y[:5]

    if len(re.sub(" ","",teht))==0:
        return {"out":False,"err":"Work task invalid"}

            # LISÄÄ PÄIVÄMÄÄRÄN TARKISTUS!
            # LISÄÄ PÄIVÄMÄÄRÄN TARKISTUS!
            # LISÄÄ PÄIVÄMÄÄRÄN TARKISTUS!
            # LISÄÄ PÄIVÄMÄÄRÄN TARKISTUS!
            # LISÄÄ PÄIVÄMÄÄRÄN TARKISTUS!
            # LISÄÄ PÄIVÄMÄÄRÄN TARKISTUS!

            # Nyt ois sitä päivämäärän tarkistusta

    y=re.sub("[^0-9]","",pv[:4])+re.sub("[^-]","",pv[4:5])+re.sub("[^0-9]","",pv[5:7])+re.sub("[^-]","",pv[7:8])+re.sub("[^0-9]","",pv[8:10])

    if len(y)!=len(pv):
        out={"out":False,"err":"Invalid date"}
        return out

    if int(y[5:7])>12 or int(y[8:10])>31:
        out={"out":False,"err":"Invalid date"}
        return out


    out=sql.add_shift(K_ID,s_aloitus,s_lopetus,teht,pv)

    return out

def sql_add_user(token,pword,name,npword,lvl):
    _x=validate_user(token,pword,2)

    if not _x["out"]:
        return _x

    out=sql.add_user(name,npword,lvl)
    return out

def sql_delete_user(token,pword,ID):
    _x=validate_user(token,pword,2)

    if not _x["out"]:
        return _x
    
    out=sql.delete_user(ID)
    return out

def validate_user(token,pword,lvl=0):
    if token not in users: return {"out":False,"err":"User invalid"}    #User not found in the users dict.
    if users[token].pword!=pword: return {"out":False,"err":"Password invalid"} #User password is incorrect.
    users[token].uAct()
    if users[token].lvl<lvl: return {"out":False,"err":"This action is restricted"}   #User doesn't possess a high enough level for this action.
    return {"out":True}

def generate_token(x="AC"):
    rd.seed()
    return enc_sha256(str(rd.randint(-2147483648,2147483647))+str(x))

def enc_sha256(h_str):
    return hlib.sha256(h_str.encode()).hexdigest()
