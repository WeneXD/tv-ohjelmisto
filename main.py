from fastapi import FastAPI
import fn

app=FastAPI()

@app.get("/")
def read_root():
    if fn.cf.has_option("WORKPLACE","Name"):
        return {"Workplace": fn.cf.get("WORKPLACE","Name")}
    else:
        return {"Workplace": "N/A"}

@app.post("/log_in/")
def log_in(ID:str,pword:str):
    x=fn.dict_decode_strings(locals())
    out=fn.log_in(x["ID"],x["pword"])
    return out

@app.post("/log_out/")
def log_out(token:str,pword:str):
    x=fn.dict_decode_strings(locals())
    out=fn.log_out(x["token"],x["pword"])
    return out

@app.get("/get_users/")
def get_users(token:str,pword:str):
    x=fn.dict_decode_strings(locals())
    out=fn.get_users(x["token"],x["pword"])
    return out

@app.get("/sql_get_users/")
async def sql_get_users(token:str,pword:str):
    x=fn.dict_decode_strings(locals())
    out=fn.sql_get_users(x["token"],x["pword"])
    return out

"""
@app.get("/sql_get_user/")
async def sql_get_user(token:str,pword:str,uid:str):
    out=fn.sql_get_user(token,pword,uid)
    return out
"""

@app.get("/get_employees/")
async def sql_get_employees(token:str,pword:str):
    x=fn.dict_decode_strings(locals())
    out=fn.sql_get_employees(x["token"],x["pword"])
    return out

@app.get("/get_shifts/")
async def sql_get_shifts(token:str,pword:str,ID:str | None = None):
    x=fn.dict_decode_strings(locals())
    out=fn.sql_get_shifts(x["token"],x["pword"],int(x["ID"]))
    return out

@app.post("/log_shift/")
async def sql_log_shift(token:str,pword:str,ID:str,aloitus:str,lopetus:str,kommentti:str):
    x=fn.dict_decode_strings(locals())
    if not x["ID"].isnumeric():
        out={"out":False,"err":"ID contains invalid characters."}
        return out
    out=fn.sql_log_shift(x["token"],x["pword"],x["ID"],x["aloitus"],x["lopetus"],x["kommentti"])
    return out

@app.post("/add_shift/")
async def sql_add_shift(token:str,pword:str,K_ID:str,s_aloitus:str,s_lopetus:str,teht:str,pv:str):
    x=fn.dict_decode_strings(locals())
    if not x["K_ID"].isnumeric:
        out={"out":False,"err":"ID contains invalid characters."}
        return out
    out=fn.sql_add_shift(x["token"],x["pword"],int(x["K_ID"]),x["s_aloitus"],x["s_lopetus"],x["teht"],x["pv"])
    return out

@app.post("/sql_add_user/")
async def sql_add_user(token:str,pword:str,name0:str,name1:str,npword:str,lvl:str):
    x=fn.dict_decode_strings(locals())
    out=fn.sql_add_user(x["token"],x["pword"],[x["name0"],x["name1"]],x["npword"],x["lvl"])
    return out

@app.post("/sql_delete_user/")
async def sql_delete_user(token:str,pword:str,ID:str):
    x=fn.dict_decode_strings(locals())
    out=fn.sql_delete_user(x["token"],x["pword"],x["ID"])
    return out

def start_app(Port=8000):
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=Port,log_level=fn.settings.LogLevelList[fn.settings.LogLevel])

if __name__=="__main__":
    start_app()