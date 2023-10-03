import tkinter as tk
from tkinter import font
import requests as req
#import time as t
#import threading as th
import base64
import re
import configparser as cparser
from pydantic import BaseModel
from os import path

cf=cparser.ConfigParser()

class Settings(BaseModel):
    ip:str="127.0.0.1"
    port:str="8000"
    addr:str=f"http://{ip}:{port}"

    def load(self):
        if not path.exists("ui_conf.ini"):
            print("augh")
            return
        
        cf.read("ui_conf.ini")
        if cf.has_section("CLIENT"):
            self.ip=cf.get("CLIENT","Host")
            self.port=cf.get("CLIENT","Port")
            self.addr=f"http://{self.ip}:{self.port}"

settings=Settings()
settings.load()

class Main(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Työvuoro-ohjelmisto")
        self.geometry("500x450")
        self.minsize(500,450)
        self.maxsize(500,450)


        self.token=""
        self.pword=""
        self.name=["",""]
        self.lvl=-1

        self.bg="#37bced"

        self.title_font=font.Font(family="Bahnschrift",size="42",weight="bold")
        self.log_font=font.Font(family="Javanese Text",size="16",weight="bold")
        self.im_font=font.Font(family="Javanese Text",size="12",weight="bold")
        self.alert_font=font.Font(family="KacstBook",size="8")

        self.pvmäärä_vcmd=(self.register(self.pvmäärä_validate),"%P")
        self.aika_vcmd=(self.register(self.aika_validate),"%P")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (Blank,LogIn,Employee,Employer,Admin):
            page_name = F.__name__
            frame = F(parent=container, cont=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LogIn")

    def show_frame(self, page_name):
        
        frame = self.frames[page_name]
        frame.tkraise()

    def pvmäärä_validate(self,P:str):
        if len(P)<=10 and len(re.sub("[^0-9-]","",P))==len(P):  #Päivämäärän pitää olla koostunut vain numeroista ja viivoista sekä ei voi mennä yli 10 merkin.
            return True
        else:
            return False
        
    def aika_validate(self,P:str):
            #Pakoittaa käyttäjän kirjoittamaan ajan muotoon hh:mm
        y=re.sub("[^0-9]","",P[:2])+re.sub("[^:]","",P[2:3])+re.sub("[^0-9]","",P[3:5])
        if len(y)==len(P) and len(P)<=5:
            return True
        else:
            return False
        
    def error_window(self,out:dict):
        self.top=tk.Toplevel()
        #self.top.protocol("WM_DELETE_WINDOW",self.close_shift_window)
        self.top.geometry("200x150")
        self.top.minsize(300,150)
        self.top.maxsize(300,150)
        self.top.title("ERROR")
        
        for x in out.keys():
            print(x)

        for x in out.values():
            print(x)

        if "err" not in out.keys():
            out["err"]="Unexpected error"

        self.error_label=tk.Label(self.top,text=f"Error: {out['err']}",font=self.im_font)
        self.error_label.place(x=1,y=1)

        tv_lisää_työvuoro_button=tk.Button(self.top,text="OK",command=self.top.destroy)
        tv_lisää_työvuoro_button.place(relx=0.5,rely=0.9,anchor="center")


class Blank(tk.Frame):
    def __init__(self,parent,cont):
        tk.Frame.__init__(self,parent)
        self.controller=cont
        label=tk.Label(self,text="juuh")
        label.pack(side="top",fill="x",pady=10)

class LogIn(tk.Frame):
    def __init__(self, parent, cont):
        tk.Frame.__init__(self, parent)
        self.cont = cont

        self.title="-"

        C=tk.Canvas(self,height=550,width=550)
        juuh = C.create_rectangle(0, 0, 500, 100, fill=cont.bg,outline="black")
        C.place(x=-1,y=-1)

        self.title_label=tk.Label(self,text="-",bg=cont.bg,font=cont.title_font)
        self.title_label.place(relx=0.5,rely=0.1,anchor="center",height=45)

        user_label=tk.Label(self,text="Käyttäjätunnus",font=cont.log_font)
        user_label.place(relx=0.5,rely=0.45,anchor="center")
        pword_label=tk.Label(self,text="Salasana",font=cont.log_font)
        pword_label.place(relx=0.5,rely=0.57,anchor="center")
        self.user_entry=tk.Entry(self,justify="center")
        self.user_entry.place(relx=0.5,rely=0.5,relwidth=0.3,anchor="center")
        self.pword_entry=tk.Entry(self,show="*",justify="center")
        self.pword_entry.place(relx=0.5,rely=0.62,relwidth=0.3,anchor="center")

        self.alert_label=tk.Label(self,text="",fg="red",font=cont.alert_font)
        self.alert_label.place(rely=0.95)

        self.login_button = tk.Button(self, text="Kirjaudu",command=self.login,bg="lightgreen")
        self.login_button.place(relx=0.5,rely=0.7,anchor="center")

        self.get_title()

    def login(self):
        user=self.user_entry.get()
        pword=self.pword_entry.get()
        self.pword_entry.delete(0,tk.END)

        if not len(user)>0 or not len(pword)>0: #Katso onko käyttäjätunnus tai salasana edes kirjoitettu
            self.alert_label.config(text="Error: ID or password missing")
            return
        
        self.get_title()

        try:    
            resp=req.post(f"{settings.addr}/log_in/?ID={b64('enc',user)}&pword={b64('enc',pword)}")
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            self.alert_label.config(text="Error: Timed Out/Server down")
            return
        except req.exceptions.HTTPError:
            self.alert_label.config(text="Error: HTTP Error")
            return
        else:
            out=resp.json()
            if 'err' in out:
                self.alert_label.config(text=f"Error:{out['err']}")
                return
            
            self.user_entry.delete(0,tk.END)
            self.cont.token=out['token']
            self.cont.pword=pword
            self.cont.lvl=out['lvl']
            self.cont.name[0]=out['name0']
            self.cont.name[1]=out['name1']

                #4debugging
            """print(self.cont.token)
            print(self.cont.pword)
            print(self.cont.lvl)
            print(self.cont.name)"""

            self.alert_label.config(text="")

            if out['lvl']==1:
                self.cont.show_frame("Employer")
                self.cont.frames['Employer'].name_label.config(text=f"{self.cont.name[0]} {self.cont.name[1]}")
                self.cont.frames['Employer'].update_employees()
                self.login_button.config(state=tk.DISABLED)
            elif out['lvl']==0:
                self.cont.show_frame("Employee")
                self.cont.frames['Employee'].name_label.config(text=f"{self.cont.name[0]} {self.cont.name[1]}")
                self.cont.frames['Employee'].get_shifts()
                self.login_button.config(state=tk.DISABLED)
            elif out['lvl']==2:
                self.cont.show_frame("Admin")
                self.cont.frames['Admin'].update_users()
                self.login_button.config(state=tk.DISABLED)
            else:
                self.alert_label.config(text="Error: Invalid user role")

    def get_title(self):
        try:
            resp=req.get(f"{settings.addr}/")
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            self.alert_label.config(text="Error: Timed Out/Server down")
            return
        except req.exceptions.HTTPError:
            self.alert_label.config(text="Error: HTTP Error")
            return
        else:
            out=resp.json()
            if 'err' in out:
                self.alert_label.config(text=f"Error:{out['err']}")
                return
            self.title=out['Workplace']
            self.title_label.config(text=out['Workplace'])
            self.cont.title(f"Työvuoro-ohjelmisto ({out['Workplace']})")

class Employer(tk.Frame):
    def __init__(self,parent,cont):
        tk.Frame.__init__(self,parent)
        self.cont=cont
        C=tk.Canvas(self,height=550,width=550)  # Luodaan canvas taustaelementeille
        yläpalkki = C.create_rectangle(0, 0, 500, 35, fill=cont.bg,outline=cont.bg)
        tietotausta = C.create_rectangle(10,45,190,260)
        C.place(x=-1,y=-1)

            #YLÄPALKKI
        tiedot_label=tk.Label(self,text="Tiedot",bg=cont.bg,fg="white",font=cont.im_font)
        tiedot_label.place(relx=0.195,rely=0.045,anchor="center",height=25)
        työntekijät_label=tk.Label(self,text="Työntekijät",bg=cont.bg,fg="white",font=cont.im_font)
        työntekijät_label.place(relx=0.6,rely=0.045,anchor="center",height=25)
        työvuorot_label=tk.Label(self,text="Työvuorot",bg=cont.bg,fg="white",font=cont.im_font)
        työvuorot_label.place(relx=0.875,rely=0.045,anchor="center",height=25)

            #TIEDOT
        self.pvmäärä=tk.Label(self,text="Pvmäärä:")
        self.pvmäärä.place(relx=0.195,y=65,anchor="center")
        self.s_aloitus=tk.Label(self,text="Suunn. aloitus:")
        self.s_aloitus.place(relx=0.195,y=100,anchor="center")
        self.s_lopetus=tk.Label(self,text="Suunn. lopetus:")
        self.s_lopetus.place(relx=0.195,y=135,anchor="center")
        #self.työvuoro=tk.Label(self,text="Työvuoro:")
        #self.työvuoro.place(relx=0.195,y=150,anchor="center")
        self.työtehtävä=tk.Label(self,text="Työtehtävä:")
        self.työtehtävä.place(relx=0.195,y=170,anchor="center")
        self.aloitus=tk.Label(self,text="Aloitus ajankohta:")
        self.aloitus.place(relx=0.195,y=205,anchor="center")
        self.lopetus=tk.Label(self,text="Lopetus ajankohta:")
        self.lopetus.place(relx=0.195,y=240,anchor="center")
        #self.ylityöt=tk.Label(self,text="Tehdyt ylityöt:")
        #self.ylityöt.place(relx=0.195,y=260,anchor="center")


        kommentti=tk.Label(self,text="Kirjattu kommentti:",font=cont.im_font)
        kommentti.place(relx=0.01,y=260)

        self.kommentti_scroll=tk.Scrollbar(self,orient="vertical")
        self.kommentti_scroll.place(x=310,y=290,height=75)

        self.kommentti=tk.Text(self,yscrollcommand=self.kommentti_scroll.set)
        self.kommentti.place(relx=0.01,y=290,width=300,height=75)
        #self.kommenttibox.insert(tk.END,"KommenttiKommenttiKommenttiKommenttiKommentti")
        self.kommentti.config(state=tk.DISABLED)
        
        self.kommentti_scroll.config(command=self.kommentti.yview)

            #LISTAT
        self.työvuorot_list=tk.Listbox(self)
        self.työvuorot_list.place(relx=0.875,rely=0.335,relheight=0.5,relwidth=0.2,anchor="center")
        self.työntekijät_list=tk.Listbox(self)
        self.työntekijät_list.place(relx=0.6,rely=0.335,relheight=0.5,relwidth=0.35,anchor="center")

        työvuorot_button=tk.Button(self,text="Hae",command=self.get_shift_info)
        työvuorot_button.place(relx=0.875,rely=0.615,relheight=0.05,relwidth=0.075,anchor="center")
        työntekijät_button=tk.Button(self,text="Hae",command=self.get_shifts)
        työntekijät_button.place(relx=0.60,rely=0.615,relheight=0.05,relwidth=0.075,anchor="center")
        työntekijät_päivitä_button=tk.Button(self,text="🗘",command=self.update_employees)
        työntekijät_päivitä_button.place(relx=0.45,rely=0.615,relheight=0.05,relwidth=0.05,anchor="center")

        self.lisää_työvuoro_button=tk.Button(self,text="Lisää työvuoro",command=self.add_shift_frame)
        self.lisää_työvuoro_button.place(relx=0.875,rely=0.665,relheight=0.05,relwidth=0.175,anchor="center")

            #KÄYTTÄJÄ
        self.name_label=tk.Label(self,text="nimi niminen",font=cont.im_font)
        self.name_label.place(relx=0.15,rely=0.94)

            #ULOSKIRJAUTUMISEN-NAPPI
        self.logout_button=tk.Button(self,text="Kirjaudu ulos",command=self.logout,bg="red")
        self.logout_button.place(relx=-0.005,rely=0.95)

        self.employees={}
        self.shifts={}
        self.employee=""

    def update_employees(self):
        self.lisää_työvuoro_button.config(bg="gray",fg="black")
        self.employee=-1
        self.reset_shift_info()
        self.työvuorot_list.delete(0,tk.END)
        out=request("get",f"{settings.addr}/get_employees/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}")

        if not out["out"]:
            if out['err']=="User invalid":
                self.cont.frames['LogIn'].alert_label.config(text="Error: Logged out for inactivity")
                self.logout()
            return
        
        self.työntekijät_list.delete(0,tk.END)
        
        for x in out["employees"]:  #0=ID, 1=Forename, 2=Surname
            self.employees[f"{x[1]} {x[2]}"]=x[0]
            self.työntekijät_list.insert(x[0],f"{x[1]} {x[2]}")

    def get_shifts(self):
        self.lisää_työvuoro_button.config(bg="lightgreen",fg="black")
        työntekijä=self.työntekijät_list.get(tk.ACTIVE)
        out=request("get",f"{settings.addr}/get_shifts/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}&ID={b64('enc',self.employees[työntekijä])}")
        if out['out']:
            self.shifts={}
            for x in out["shifts"]:
                self.shifts[x[6]]=[]    #Create a dictkey with the date
                for y in x:
                    self.shifts[x[6]].append(y) #Fill the dictkey's list with the values.
        elif out['err']=="User invalid":
            self.cont.frames['LogIn'].alert_label.config(text="Error: Logged out for inactivity")
            self.logout()

        self.employee=työntekijä

        shift_list=[]
        shift_list=list(self.shifts.keys())
        shift_list.sort(reverse=True)
        self.työvuorot_list.delete(0,tk.END)

        for id, x in enumerate(shift_list):
            self.työvuorot_list.insert(id,x)
            
            #Hulluksihan tässä tulee, huhhu

    def get_shift_info(self):
        tv_pvmäärä=self.työvuorot_list.get(tk.ACTIVE)
        if tv_pvmäärä not in self.shifts:
            return
        
        työvuoro=[]
        for x in self.shifts[tv_pvmäärä]:
            työvuoro.append(x)


        print(työvuoro)

        työvuoro_tila=" - "

        tv_ajat=[]

        if työvuoro[3] is None:
            työvuoro_tila="Ei aloitettu"
        else:
            for x in range(1,5):
                _x=työvuoro[x].split(":")
                tv_ajat.append(_x)
            print(tv_ajat)

        for _x, x in enumerate(työvuoro):
            if x is None:
                työvuoro[_x]=""


        self.pvmäärä.config(text=f"Pvmäärä: {tv_pvmäärä}")
        self.s_aloitus.config(text=f"Suunn. aloitus: {työvuoro[1]}")
        self.s_lopetus.config(text=f"Suunn. lopetus: {työvuoro[2]}")
        #self.työvuoro.config(text=f"Työvuoro: {työvuoro_tila}")
        self.työtehtävä.config(text=f"Työtehtävä: {työvuoro[5]}")
        self.aloitus.config(text=f"Aloitus ajankohta: {työvuoro[3]}")
        self.lopetus.config(text=f"Lopetus ajankohta: {työvuoro[4]}")
        #self.ylityöt.config(text=f"Tehdyt ylityöt: {työvuoro[7]}")
        self.kommentti.config(state=tk.NORMAL)
        self.kommentti.delete("1.0","end")
        self.kommentti.insert(tk.END,työvuoro[8])
        self.kommentti.config(state=tk.DISABLED)


        """self.pvmäärä=tk.Label(self,text="Pvmäärä: 31.12.2000")
        self.pvmäärä.place(relx=0.195,y=60,anchor="center")
        self.s_aloitus=tk.Label(self,text="Suunn. aloitus: 44:44")
        self.s_aloitus.place(relx=0.195,y=90,anchor="center")
        self.s_lopetus=tk.Label(self,text="Suunn. lopetus: 44:44")
        self.s_lopetus.place(relx=0.195,y=120,anchor="center")
        self.työvuoro=tk.Label(self,text="Työvuoro: Jätetty kesken")
        self.työvuoro.place(relx=0.195,y=150,anchor="center")
        self.työtehtävä=tk.Label(self,text="Työtehtävä: Tiskaaminen")
        self.työtehtävä.place(relx=0.195,y=180,anchor="center")
        self.aloitus=tk.Label(self,text="Aloitus ajankohta: 44:44")
        self.aloitus.place(relx=0.195,y=210,anchor="center")
        self.lopetus=tk.Label(self,text="Lopetus ajankohta: 44:44")
        self.lopetus.place(relx=0.195,y=240,anchor="center")
        self.ylityöt=tk.Label(self,text="Tehdyt ylityöt: 0min")
        self.ylityöt.place(relx=0.195,y=270,anchor="center")"""

    def add_shift_frame(self):
        format_color="gray"
        self.lisää_työvuoro_button.config(bg="lightgreen",fg="black")
        if self.employee==-1:
            return
        self.top=tk.Toplevel()
        #self.top.overrideredirect(True)
        self.top.protocol("WM_DELETE_WINDOW",self.close_shift_window)
        self.top.geometry("400x300")
        self.top.minsize(400,300)
        self.top.maxsize(400,300)
        self.top.title("LISÄÄ TYÖVUORO")

        im_font=font.Font(family="Javanese Text",size="11",weight="bold")

        C=tk.Canvas(self.top,height=300,width=400)  # Luodaan canvas taustaelementeille
        yläpalkki = C.create_rectangle(0, 0, 99999999, 35, fill=self.cont.bg,outline=self.cont.bg)
        tietotausta = C.create_rectangle(10,45,390,260)
        C.place(x=0,y=0)


        self.tv_työntekijä_label=tk.Label(self.top,bg=self.cont.bg,fg="white",text=f"Työntekijä: {self.työntekijät_list.get(tk.ACTIVE)}",font=self.cont.im_font)
        self.tv_työntekijä_label.place(relx=0.01,rely=0.03,height=20)

        tv_pvmäärä_label=tk.Label(self.top,text="Pvmäärä:",font=im_font)
        tv_pvmäärä_label.place(relx=0.14,rely=0.225,anchor="center",height=20)
        self.tv_pvmäärä_entry=tk.Entry(self.top,validate="key",validatecommand=self.cont.pvmäärä_vcmd)
        self.tv_pvmäärä_entry.place(relx=0.400,rely=0.22,anchor="center",height=20)
        tv_pvmäärä_format_label=tk.Label(self.top,text="(YYYY-MM-DD)",fg=format_color)
        tv_pvmäärä_format_label.place(relx=0.68,rely=0.22,anchor="center",height=20)

        tv_s_aloitus_label=tk.Label(self.top,text="Suunn. aloitus:",font=im_font)
        tv_s_aloitus_label.place(relx=0.18,rely=0.325,anchor="center",height=20)
        self.tv_s_aloitus_entry=tk.Entry(self.top,justify="center",validate="key",validatecommand=self.cont.aika_vcmd)
        self.tv_s_aloitus_entry.place(relx=0.425,rely=0.32,anchor="center",height=20,width=70)
        tv_s_aloitus_format_label=tk.Label(self.top,text="(HH:MM)",fg=format_color)
        tv_s_aloitus_format_label.place(relx=0.6,rely=0.32,anchor="center",height=20)

        tv_s_lopetus_label=tk.Label(self.top,text="Suunn. lopetus:",font=im_font)
        tv_s_lopetus_label.place(relx=0.18,rely=0.425,anchor="center",height=20)
        self.tv_s_lopetus_entry=tk.Entry(self.top,justify="center",validate="key",validatecommand=self.cont.aika_vcmd)
        self.tv_s_lopetus_entry.place(relx=0.425,rely=0.42,anchor="center",height=20,width=70)
        tv_s_lopetus_format_label=tk.Label(self.top,text="(HH:MM)",fg=format_color)
        tv_s_lopetus_format_label.place(relx=0.6,rely=0.42,anchor="center",height=20)

        tv_työtehtävä_label=tk.Label(self.top,text="Työtehtävä:",font=im_font)
        tv_työtehtävä_label.place(relx=0.16,rely=0.525,anchor="center",height=20)
        self.tv_työtehtävä_entry=tk.Entry(self.top)
        self.tv_työtehtävä_entry.place(relx=0.435,rely=0.52,anchor="center",height=20,width=125)

        tv_lisää_työvuoro_button=tk.Button(self.top,text="Lisää työvuoro",command=self.add_shift)
        tv_lisää_työvuoro_button.place(relx=0.5,rely=0.925,anchor="center")

        self.lisää_työvuoro_button.config(state=tk.DISABLED)
        self.logout_button.config(state=tk.DISABLED)

    def add_shift(self):
        pvmäärä=self.tv_pvmäärä_entry.get()
        aloitus_aika=self.tv_s_aloitus_entry.get()
        lopetus_aika=self.tv_s_lopetus_entry.get()
        työtehtävä=self.tv_työtehtävä_entry.get()

        out=request("post",f"{settings.addr}/add_shift/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}&K_ID={b64('enc',self.employees[self.employee])}&s_aloitus={b64('enc',aloitus_aika)}&s_lopetus={b64('enc',lopetus_aika)}&teht={b64('enc',työtehtävä)}&pv={b64('enc',pvmäärä)}")

        if out["out"]:
            self.lisää_työvuoro_button.config(bg="#000eee000",fg="#000666000")
            self.close_shift_window()
        else:
            self.lisää_työvuoro_button.config(bg="red")
            self.cont.error_window(out)

    def close_shift_window(self):
        self.top.destroy()
        self.logout_button.config(state=tk.NORMAL)
        self.lisää_työvuoro_button.config(state=tk.NORMAL)

    def reset_shift_info(self):
        self.pvmäärä.config(text=f"Pvmäärä:")
        self.s_aloitus.config(text=f"Suunn. aloitus:")
        self.s_lopetus.config(text=f"Suunn. lopetus:")
        #self.työvuoro.config(text=f"Työvuoro:")
        self.työtehtävä.config(text=f"Työtehtävä:")
        self.aloitus.config(text=f"Aloitus ajankohta:")
        self.lopetus.config(text=f"Lopetus ajankohta:")
        #self.ylityöt.config(text=f"Tehdyt ylityöt:")
        self.kommentti.config(state=tk.NORMAL)
        self.kommentti.delete("1.0","end")
        self.kommentti.config(state=tk.DISABLED)

    def logout(self):
        try:
            resp=req.post(f"{settings.addr}/log_out/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}")
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            print("Error: Timed Out/Server down")
            return {"out":False,"err":"Timed Out/Server down"}
        except req.exceptions.HTTPError:
            print("Error: HTTP Error")
            return {"out":False,"err":"HTTP Error"}
        else:
            out=resp.json()
            if 'err' in out:
                print(f"Error:{out['err']}")
            self.cont.frames['LogIn'].login_button.config(state=tk.NORMAL)
            self.cont.show_frame("LogIn")
            self.cont.token=""
            self.cont.lvl=-1
            self.cont.name=["",""]
            self.cont.pword=""
            self.reset_shift_info()

class Employee(tk.Frame):
    def __init__(self,parent,cont):
        tk.Frame.__init__(self,parent)
        self.cont=cont
        C=tk.Canvas(self,height=550,width=550)  # Luodaan canvas taustaelementeille
        yläpalkki = C.create_rectangle(0, 0, 500, 35, fill=cont.bg,outline=cont.bg)
        tietotausta = C.create_rectangle(10,45,190,260)
        C.place(x=-1,y=-1)

            #YLÄPALKKI
        tiedot_label=tk.Label(self,text="Tiedot",bg=cont.bg,fg="white",font=cont.im_font)
        tiedot_label.place(relx=0.195,rely=0.045,anchor="center",height=25)
        työvuorot_label=tk.Label(self,text="Työvuorot",bg=cont.bg,fg="white",font=cont.im_font)
        työvuorot_label.place(relx=0.8,rely=0.045,anchor="center",height=25)

            #TIEDOT
        self.pvmäärä=tk.Label(self,text="Pvmäärä:")
        self.pvmäärä.place(relx=0.195,y=60,anchor="center")
        self.s_aloitus=tk.Label(self,text="Suunn. aloitus:")
        self.s_aloitus.place(relx=0.195,y=90,anchor="center")
        self.s_lopetus=tk.Label(self,text="Suunn. lopetus:")
        self.s_lopetus.place(relx=0.195,y=120,anchor="center")
        self.työtehtävä=tk.Label(self,text="Työtehtävä:")
        self.työtehtävä.place(relx=0.195,y=150,anchor="center")
        self.aloitus=tk.Label(self,text="Aloitus ajankohta:")
        self.aloitus.place(relx=0.195,y=180,anchor="center")
        self.aloitus_entry=tk.Entry(self,justify="center",validate="key",validatecommand=self.cont.aika_vcmd)
        self.aloitus_entry.place(relx=0.195,y=200,anchor="center",width=70)
        self.lopetus=tk.Label(self,text="Lopetus ajankohta:")
        self.lopetus.place(relx=0.195,y=220,anchor="center")
        self.lopetus_entry=tk.Entry(self,justify="center",validate="key",validatecommand=self.cont.aika_vcmd)
        self.lopetus_entry.place(relx=0.195,y=240,anchor="center",width=70)


            #KOMMENTTI
        kommentti=tk.Label(self,text="Kommentti:",font=cont.im_font)
        kommentti.place(relx=0.01,y=260)

        self.kommentti_scroll=tk.Scrollbar(self,orient="vertical")
        self.kommentti_scroll.place(x=310,y=290,height=75)

        self.kommenttibox=tk.Text(self,yscrollcommand=self.kommentti_scroll.set)
        self.kommenttibox.place(relx=0.01,y=290,width=300,height=75)

        self.kommentti_scroll.config(command=self.kommenttibox.yview)

        self.kommenttibox.bind('<KeyRelease>',self.limit_comment)
        self.kommenttibox.bind('<KeyPress>',self.limit_comment)

            #NAPPEI

        työvuorot_päivitä_button=tk.Button(self,text="🗘",command=self.get_shifts_reset)
        työvuorot_päivitä_button.place(relx=0.675,rely=0.615,relheight=0.05,relwidth=0.05,anchor="center")

        self.kirjaa_button=tk.Button(self,text="Kirjaa",command=self.log_shift,bg="lightgreen")
        self.kirjaa_button.place(relx=0.45,rely=0.82,width=70)   

            #LISTAT
        self.työvuorot_list=tk.Listbox(self)
        self.työvuorot_list.place(relx=0.8,rely=0.335,relheight=0.5,relwidth=0.3,anchor="center")

        hae_button=tk.Button(self,text="Hae",command=self.get_shift_info,bg="lightgreen")
        hae_button.place(relx=0.8,rely=0.62,width=50,anchor="center")


            #KÄYTTÄJÄ
        self.name_label=tk.Label(self,text="nimi niminen",font=cont.im_font)
        self.name_label.place(relx=0.15,rely=0.94)

            #ULOSKIRJAUTUMISEN-NAPPI
        logout_button=tk.Button(self,text="Kirjaudu ulos",command=self.logout,bg="red")
        logout_button.place(relx=-0.005,rely=0.95)

        self.shifts={}
        self.selected_shift=-1

    def limit_comment(self,value):
        if len(self.kommenttibox.get("1.0","end-1c"))>200:
            self.kommenttibox.delete("end-2c")

    def log_shift(self):
        if self.selected_shift==-1: #Pitää olla työvuoro valittuna
            return
        self.kirjaa_button.config(fg="black")
        kommentti=self.kommenttibox.get("1.0","end-1c")
        aloitus_aika=self.aloitus_entry.get()
        lopetus_aika=self.lopetus_entry.get()

        tv_ID=self.selected_shift

        print(tv_ID)

        aika=[]

        for x in [aloitus_aika,lopetus_aika]:
            if len(x)<4:    #Pakko olla ajat, jotta voi kirjata.
                self.kirjaa_button.config(bg="red")
                return
            _x=x.split(":")
            _x[0]=str(clamp(int(_x[0]),0,23))
            _x[1]=str(clamp(int(_x[1]),0,59))
            for yid, y in enumerate(_x):
                print(len(y))
                if len(y)==1:
                    _x[yid]=f"0{y}"
            aika.append(f"{_x[0]}:{_x[1]}") #Tuntien on pakko olla 0-24 välillä ja minuuttien 0-59 välillä.
        
        print(kommentti, aloitus_aika, lopetus_aika)
        print(aika)

        aloitus_aika=aika[0]
        lopetus_aika=aika[1]

        self.aloitus_entry.delete(0,tk.END)
        self.lopetus_entry.delete(0,tk.END)
        self.aloitus_entry.insert(tk.END,aloitus_aika)
        self.lopetus_entry.insert(tk.END,lopetus_aika)


        o=re.sub(" ","",kommentti)

        if len(o)<1:
            self.kirjaa_button.config(bg="red")
            return  #Pakko olla kommentti, jotta voi kirjata.

        out=request("post",f"{settings.addr}/log_shift/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}&ID={b64('enc',tv_ID)}&aloitus={b64('enc',aloitus_aika)}&lopetus={b64('enc',lopetus_aika)}&kommentti={b64('enc',kommentti)}")

        self.get_shifts()

        if not out["out"]:
            if out['err']=="User invalid":
                self.cont.frames['LogIn'].alert_label.config(text="Error: Logged out for inactivity")
                self.logout()
            self.kirjaa_button.config(bg="red")
        else:
            self.kirjaa_button.config(bg="#000eee000",fg="#000666000")

    def get_shifts(self):
        self.kirjaa_button.config(bg="lightgreen",fg="black")
        out=request("get",f"{settings.addr}/get_shifts/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}")
        
        if not out["out"]:
            if out['err']=="User invalid":
                self.cont.frames['LogIn'].alert_label.config(text="Error: Logged out for inactivity")
                self.logout()
            return

        if out['out']:
            self.shifts={}
            for x in out["shifts"]:
                self.shifts[x[6]]=[]    #Create a dictkey with the date
                for y in x:
                    self.shifts[x[6]].append(y) #Fill the dictkey's list with the values.

        shift_list=[]
        shift_list=list(self.shifts.keys())
        shift_list.sort(reverse=True)
        self.työvuorot_list.delete(0,tk.END)

        for id, x in enumerate(shift_list):
            self.työvuorot_list.insert(id,x)

    def get_shifts_reset(self):
        self.get_shifts()
        self.reset_shift_info()

    def get_shift_info(self):
        tv_pvmäärä=self.työvuorot_list.get(tk.ACTIVE)
        if tv_pvmäärä not in self.shifts:
            return
        
        #print(tv_pvmäärä)

        työvuoro=[]
        for x in self.shifts[tv_pvmäärä]:
            työvuoro.append(x)

        #print(työvuoro)

        if työvuoro[3] is None:
            työvuoro_tila="Ei aloitettu"

        for _x, x in enumerate(työvuoro):
            if x is None:
                työvuoro[_x]=""

        self.selected_shift=työvuoro[0] #Laittaa selected_shift -muuttujan tällä hetkellä avatuksi työvuoroksi.
        #print(self.selected_shift)

        self.pvmäärä.config(text=f"Pvmäärä: {tv_pvmäärä}")
        self.s_aloitus.config(text=f"Suunn. aloitus: {työvuoro[1]}")
        self.s_lopetus.config(text=f"Suunn. lopetus: {työvuoro[2]}")
        #self.työvuoro.config(text=f"Työvuoro: {työvuoro_tila}")
        self.työtehtävä.config(text=f"Työtehtävä: {työvuoro[5]}")
        self.aloitus_entry.delete(0,tk.END)
        self.lopetus_entry.delete(0,tk.END)
        self.aloitus_entry.insert(tk.END,työvuoro[3])
        self.lopetus_entry.insert(tk.END,työvuoro[4])
        #self.ylityöt.config(text=f"Tehdyt ylityöt: {työvuoro[7]}")
        self.kommenttibox.delete("1.0","end")
        self.kommenttibox.insert(tk.END,työvuoro[8])

        """
        self.pv=tk.Label(self,text="Pvmäärä: 1999.1.1")
        self.pv.place(relx=0.195,y=60,anchor="center")
        self.s_aloitus=tk.Label(self,text="Suunn. aloitus: 44:44")
        self.s_aloitus.place(relx=0.195,y=90,anchor="center")
        self.s_lopetus=tk.Label(self,text="Suunn. lopetus: 44:44")
        self.s_lopetus.place(relx=0.195,y=120,anchor="center")
        self.työtehtävä=tk.Label(self,text="Työtehtävä: Tiskaaminen")
        self.työtehtävä.place(relx=0.195,y=150,anchor="center")
        self.aloitus=tk.Label(self,text="Aloitus ajankohta:")
        self.aloitus.place(relx=0.195,y=180,anchor="center")
        self.aloitus_entry=tk.Entry(self,justify="center",validate="key",validatecommand=self.cont.aika_vcmd)
        self.aloitus_entry.place(relx=0.195,y=200,anchor="center",width=70)
        self.lopetus=tk.Label(self,text="Lopetus ajankohta:")
        self.lopetus.place(relx=0.195,y=220,anchor="center")
        self.lopetus_entry=tk.Entry(self,justify="center",validate="key",validatecommand=self.cont.aika_vcmd)
        self.lopetus_entry.place(relx=0.195,y=240,anchor="center",width=70)

        kommentti=tk.Label(self,text="Kommentti:",font=cont.im_font)
        kommentti.place(relx=0.01,y=260)

        self.kommenttibox=tk.Text(self)
        self.kommenttibox.place(relx=0.01,y=290,width=300,height=75)"""

    def reset_shift_info(self):
        self.pvmäärä.config(text=f"Pvmäärä:")
        self.s_aloitus.config(text=f"Suunn. aloitus:")
        self.s_lopetus.config(text=f"Suunn. lopetus:")
        #self.työvuoro.config(text=f"Työvuoro: {työvuoro_tila}")
        self.työtehtävä.config(text=f"Työtehtävä:")
        self.aloitus_entry.delete(0,tk.END)
        self.lopetus_entry.delete(0,tk.END)
        #self.ylityöt.config(text=f"Tehdyt ylityöt: {työvuoro[7]}")
        self.kommenttibox.delete("1.0","end")

    def logout(self):
        try:
            resp=req.post(f"{settings.addr}/log_out/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}")
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            print("Error: Timed Out/Server down")
            return
        except req.exceptions.HTTPError:
            print("Error: HTTP Error")
            return
        else:
            out=resp.json()
            self.cont.token=""
            self.cont.lvl=-1
            self.cont.name=["",""]
            self.cont.pword=""
            if 'err' in out:
                print(f"Error:{out['err']}")
            self.cont.frames['LogIn'].login_button.config(state=tk.NORMAL)
            self.cont.show_frame("LogIn")

class Admin(tk.Frame):
    def __init__(self,parent,cont):
        tk.Frame.__init__(self,parent)
        self.cont=cont
        C=tk.Canvas(self,height=550,width=550)  # Luodaan canvas taustaelementeille
        yläpalkki = C.create_rectangle(0, 0, 500, 70, fill="red",outline="red")
        #tietotausta = C.create_rectangle(10,45,190,260)
        C.place(x=-1,y=-1)

        tiedot_label=tk.Label(self,text="YLLÄPITÄJÄ",bg="red",fg="white",font=cont.title_font)
        tiedot_label.place(relx=0.5,rely=0.07,anchor="center",height=65)

        im_font=font.Font(family="Javanese Text",size="11",weight="bold")

        etunimi_label=tk.Label(self,text="Etunimi",font=im_font)
        etunimi_label.place(relx=0.2,rely=0.225,anchor="center",height=20)
        self.etunimi_entry=tk.Entry(self,justify="center")
        self.etunimi_entry.place(relx=0.2,rely=0.265,anchor="center",height=20)
        sukunimi_label=tk.Label(self,text="Sukunimi",font=im_font)
        sukunimi_label.place(relx=0.2,rely=0.325,anchor="center",height=20)
        self.sukunimi_entry=tk.Entry(self,justify="center")
        self.sukunimi_entry.place(relx=0.2,rely=0.365,anchor="center")
        salasana_label=tk.Label(self,text="Salasana:",font=im_font)
        salasana_label.place(relx=0.2,rely=0.425,anchor="center",height=20)
        self.salasana_entry=tk.Entry(self,show="*",justify="center")
        self.salasana_entry.place(relx=0.2,rely=0.465,anchor="center",height=20)
        var_salasana_label=tk.Label(self,text="Varmista salasana:",font=im_font)
        var_salasana_label.place(relx=0.2,rely=0.525,anchor="center",height=20)
        self.var_salasana_entry=tk.Entry(self,justify="center",show="*")
        self.var_salasana_entry.place(relx=0.2,rely=0.565,anchor="center",height=20)

        roolit=["Työntekijä","Työnantaja"]
        self.rooli=tk.StringVar()
        self.rooli.set("Työntekijä")

        roolimenu=tk.OptionMenu(self,self.rooli,*roolit)
        roolimenu.place(relx=0.2,rely=0.635,anchor="center")

        lisää_käyttäjä_button=tk.Button(self,text="Lisää",command=self.add_user)
        lisää_käyttäjä_button.place(relx=0.2,rely=0.73,anchor="center",relheight=0.05,relwidth=0.1)
        
        self.käyttäjät_list=tk.Listbox(self)
        self.käyttäjät_list.place(relx=0.75,rely=0.45,relheight=0.5,relwidth=0.4,anchor="center")

        käyttäjät_päivitä_button=tk.Button(self,text="🗘",command=self.update_users)
        käyttäjät_päivitä_button.place(relx=0.575,rely=0.73,relheight=0.05,relwidth=0.05,anchor="center")
        käyttäjät_poista_button=tk.Button(self,text="Poista",command=self.delete_user)
        käyttäjät_poista_button.place(relx=0.75,rely=0.73,relheight=0.05,relwidth=0.1,anchor="center")

        self.logout_button=tk.Button(self,text="Kirjaudu ulos",command=self.logout,bg="red")
        self.logout_button.place(relx=-0.005,rely=0.95)

        self.users={}
        self.employee=""

    def add_user(self):
        etunimi=self.etunimi_entry.get()
        sukunimi=self.sukunimi_entry.get()
        pword=self.salasana_entry.get()
        verify_pword=self.var_salasana_entry.get()
        for x in [etunimi,sukunimi]:
            if len(x)<2:
                return
            
        for x in [pword,verify_pword]:
            if len(x)<6:
                return

        if pword!=verify_pword:
            return
        
        rooli=self.rooli.get()

        print(rooli)

        for idx, x in enumerate(["Työntekijä","Työnantaja"]):
            if rooli==x:
                rooli=idx
                break
        print(rooli)

        names=[b64("enc",etunimi),b64("enc",sukunimi)]

        request("post",f"{settings.addr}/sql_add_user/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}&name0={names[0]}&name1={names[1]}&npword={b64('enc',pword)}&lvl={b64('enc',rooli)}/")

        self.salasana_entry.delete(0,tk.END)
        self.var_salasana_entry.delete(0,tk.END)

        self.update_users()

    def delete_user(self):
        käyttäjä=self.käyttäjät_list.get(tk.ACTIVE)
        x=käyttäjä.split(" | ")
        ID=self.users[x[1]]

        request("post",f"{settings.addr}/sql_delete_user/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}&ID={b64('enc',ID)}")

        self.update_users()

    def update_users(self):
        self.employee=-1
        out=request("get",f"{settings.addr}/sql_get_users/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}")

        if not out["out"]:
            if out['err']=="User invalid":
                self.cont.frames['LogIn'].alert_label.config(text="Error: Logged out for inactivity")
                self.logout()
            return
        
        print(out)

        self.käyttäjät_list.delete(0,tk.END)
        
        for x in out["users"]:  #0=ID, 1=Forename, 2=Surname
            self.users[f"{x[1]} {x[2]}"]=x[0]
            if x[3]==0:
                self.käyttäjät_list.insert(x[0],f"{x[0]} | {x[1]} {x[2]}")
            else:
                self.käyttäjät_list.insert(x[0],f"[TA] {x[0]} | {x[1]} {x[2]}")

    def logout(self):
        try:
            resp=req.post(f"{settings.addr}/log_out/?token={b64('enc',self.cont.token)}&pword={b64('enc',self.cont.pword)}")
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            print("Error: Timed Out/Server down")
            return
        except req.exceptions.HTTPError:
            print("Error: HTTP Error")
            return
        else:
            out=resp.json()
            if 'err' in out:
                print(f"Error:{out['err']}")
            self.cont.frames['LogIn'].login_button.config(state=tk.NORMAL)
            self.cont.show_frame("LogIn")
            self.cont.token=""
            self.cont.lvl=-1
            self.cont.name=["",""]
            self.cont.pword=""
            self.etunimi_entry.delete(0,tk.END)
            self.sukunimi_entry.delete(0,tk.END)
            self.salasana_entry.delete(0,tk.END)
            self.var_salasana_entry.delete(0,tk.END)

def request(type,link):
    if type=="get":
        try:
            resp=req.get(link)
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            print("Error: Timed Out/Server down")
            return {"out":False,"err":"Timed Out/Server down"}
        except req.exceptions.HTTPError:
            print("Error: HTTP Error")
            return {"out":False,"err":"HTTP Error"}
        else:
            out=resp.json()
            if 'err' in out:
                print(f'Error:{out["err"]}')
                return out
            
            return out
    elif type=="post":
        try:    
            resp=req.post(link)
            resp.raise_for_status()
        except (req.exceptions.ConnectionError,req.exceptions.Timeout):
            print("Error: Timed Out/Server down")
            return {"out":False,"err":"Timed Out/Server down"}
        except req.exceptions.HTTPError:
            print("Error: HTTP Error")
            return {"out":False,"err":"HTTP Error"}
        else:
            out=resp.json()
            if 'err' in out:
                print(f"Error:{out['err']}")
                return out
            
            return out

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

def b64(x,y):
    y=str(y)
    if x=="enc": mBytes=y.encode("utf-8"); b64Bytes=base64.b64encode(mBytes); return b64Bytes.decode("utf-8")
    elif x=="dec": b64Bytes=y.encode("utf-8"); mBytes=base64.b64decode(b64Bytes); return mBytes.decode("utf-8")

if __name__=="__main__":
    app = Main()
    app.mainloop()
