import gc
import os

def terminal_color(txt,col=33):
    return "\033[" + str(col) + "m" + str(txt) + "\033[m" 

def printBar(num1,num2,col):
    #if num1/num2 < 
    print("[",end="")
    print((("\033[" + str(col) + "m#\033[m")*num1),end="")
    print(" " * num2,end="") 
    print("]  ",end="")

def print_stats():
    bar100 = 30
    
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = F/T*100
    
    if P < 20:
        col = 31
    elif P < 40:
        col = 33
    else:
        col = 32
    
    b1 = T / bar100
    print("Volna  RAM : ", end="")
    printBar(int(F / b1), bar100 - int(F / b1),col)
    print(terminal_color('{0:.3f} kB  =  '.format(F / 1000) + '{0:.1f}%'.format(P),col))
    
    
    
    
    s = os.statvfs('//')
    flash100 = (s[0]*s[2])/1048576
    flash = (s[0]*s[3])/1048576
    P = flash/flash100*100
    
    if P < 20:
        col = 31
    elif P < 40:
        col = 33
    else:
        col = 32
    
    b1 = flash100 / bar100
    print("Volna Flash: ", end="")
    printBar(int(flash / b1), bar100 - int(flash / b1),col)
    print(terminal_color(' {0:.3f} MB  =  '.format(flash) +  '{0:.1f}%'.format(P),col))
    
