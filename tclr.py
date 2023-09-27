class clr:
    warn='\033[91m' #Red
    value='\033[96m'    #Cyan
    file='\033[95m' #Pink
    ok='\033[92m'   #Green

if __name__=="__main__":    #Print colors if ran on its own.
    juuh={}
    diih=dict(clr.__dict__.items())
    for x,y in diih.items():
        if x[0:2]!="__":
            print(f"{y}{x}")

    print("\033[97m",end="")