import os
import time
import network
import ujson
import ubinascii
from machine import I2C, Pin
from micropython import alloc_emergency_exception_buf

alloc_emergency_exception_buf(128)


# Inicializace I2C OLED a Framebufferu
import framebuf

display_connected = False
height = 64
width = 128
pages = height // 8
buffer = bytearray(pages * width)
fbuf = framebuf.FrameBuffer(buffer, width, height, framebuf.MONO_VLSB)

L_v_joyX = 0
L_v_joyY = 0
L_v_press = 0
R_v_joyX = 0
R_v_joyY = 0
R_v_press = 0
display = None


def remove_diacritics(s):
    diacritics = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e', 'í': 'i', 'ň': 'n',
        'ó': 'o', 'ř': 'r', 'š': 's', 'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
        'Á': 'A', 'Č': 'C', 'Ď': 'D', 'É': 'E', 'Ě': 'E', 'Í': 'I', 'Ň': 'N',
        'Ó': 'O', 'Ř': 'R', 'Š': 'S', 'Ť': 'T', 'Ú': 'U', 'Ů': 'U', 'Ý': 'Y', 'Ž': 'Z'
    }
    return ''.join(diacritics.get(c, c) for c in s)


# Nacteni konfigurace oled a hlavniho I2C
def read_oled_config(filename="oled.cfg"):
    scl_pin, sda_pin = None, None
    try:
        with open(filename, "r") as f:
            content = f.read()
        # Normalizace koncu radku a rozdeleni na radky:
        lines = content.replace("\r\n", "\r").replace("\n", "\r").split("\r")
        for line in lines:
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()
                if key == "OLED_SCL":
                    scl_pin = int(value)
                elif key == "OLED_SDA":
                    sda_pin = int(value)
    except Exception as e:
        print("Chyba pri cteni konfiguracniho souboru:", e)
    return scl_pin, sda_pin


# Funkce pro vytvoreni I2C rozhrani a jeho pojmenovani
def create_oled_i2c():
    global display, display_connected, buffer    
    
    scl, sda = read_oled_config()
    if scl is None or sda is None:
        print("Konfiguracni soubor pro OLED nebyl nalezen, nebo obsahuje neplatna data !")
        print("Nakonfigurujte piny pro pripojeni OLED displaye.")
        return None
    
    try:
        i2c_name = f"i2c_{scl}_{sda}"  # Nazev podle pinu
        globals()[i2c_name] = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)  # Vytvoreni HW I2C
        print(f"Vytvorena hlavni I2C sbernice: {i2c_name}")
        devices = globals()[i2c_name].scan()
        #print(devices)
        # Prohledani I2C sbernice aby se vedelo jestli je OLED pripojen
        if 60 in devices:
            print("Display SSD1306 nebo SSD1309 pripojen")
            display_connected = True
            from oled import OLED128x64
            display = OLED128x64(128, 64, globals()[i2c_name], buffer, rotate=False)    
        elif 63 in devices:
            print("Display ST7567 pripojen")
            display_connected = True
            import st7567
            display = st7567.ST7567_I2C(128, 64, globals()[i2c_name], buffer)
        else:
            print("Display nenalezen!")
            print(f"Pripojte OLED display na piny SCL = {scl} a SDA = {sda}")
      
    except Exception as e:
        print("Nastal problem s vytvorenim I2C sbernice pro OLED: ", e)
        return None
    
    return globals()[i2c_name]

# Nacteni konfigurace I2C pro Oled a jeho inicializace
create_oled_i2c() 





gc.collect()

# Zapinani WIFI
fbuf.fill(0)
fbuf.text(str("Zapinani WIFI"), 12, 28, 1)

if display_connected == True:
    display.show()



import wifimgr

wlan = wifimgr.get_connection()
gc.collect()

# Vypis aktualniho nastaveni WIFI na OLED

sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)

WIFI_SSID = "Nepripojeno"
WIFI_IP = "0.0.0.0"

if sta.active():
    WIFI_SSID = sta.config("essid")
    WIFI_IP = sta.ifconfig()[0]

if ap.active():
    WIFI_SSID = ap.config("essid")
    WIFI_IP = ap.ifconfig()[0]

fbuf.fill(0)
fbuf.text("Nastaveni WIFI", 11, 0, 1)
fbuf.text("SSID:" + remove_diacritics(WIFI_SSID), 0, 22, 1)
if len(WIFI_IP) > 13:
    fbuf.text(WIFI_IP, 0, 34, 1)
else:
    fbuf.text("IP:" + WIFI_IP, 0, 34, 1)

if display_connected == True:
    display.show()



def stop_code():
    try:
        on_exit()
    except:
        #print('Funkce pro ukonceni programu nebyla definovana')
        time.sleep_ms(0)

def run_code():
    try:
        gc.collect()
        exec(open("idecode").read())
    except KeyboardInterrupt:
        print('Zastaveni programu')
        gc.collect()
        stop_code()

def list_files(path="/"):
    files = [
        "{0}/".format(name)
        if os.stat(path + "/" + name)[0] & 0o170000 == 0o040000
        else name
        for name in os.listdir(path)
    ]

    files.sort()
    content = ";".join(files)

    print("*FL*" + content + "#FL#")

def list_wifi():
    print("*wifi*" + str(wifimgr.read_profiles()) + "#wifi#")



gc.collect()


# Start WWW serveru
from web_server import WebServer

webserver = WebServer(web_folder='/www', port=80)


# Dynamicky nacitany toolbox
@webserver.handle('/toolbox.xml')
def handle_toolbox(client, path, request):
    # Zjistíme typ procesoru
    machine = os.uname().machine
    
    if "ESP32C3" in machine:
        print("Detekovan procesor ESP32C3")
        dynamic_path = "/toolbox_ESP32C3.xml"
    elif "ESP32S3" in machine:
        print("Detekovan procesor ESP32S3")
        dynamic_path = "/toolbox_ESP32S3.xml"
    elif "ESP32" in machine:
        print("Detekovan procesor ESP32")
        dynamic_path = "/toolbox_ESP32.xml"
    else:
        print("Neznámý procesor")
        dynamic_path = "/toolbox_ESP32.xml"
        
    webserver.serve_file(client, dynamic_path)


@webserver.handle('/*FB')
def handle_fb(client, path, request):
    global buffer
    try:
        client.write("HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n\r\n".encode("utf-8"))
        client.write(buffer)
    except OSError as e:
        print("OSError:", e)

@webserver.handle('/*JOY')
def handle_joy(client, path, request):
    global L_v_joyX, L_v_joyY, R_v_joyX, R_v_joyY, L_v_press, R_v_press

    R_v_joyX = path.split(";")[1]
    R_v_joyY = path.split(";")[2]
    R_v_press = path.split(";")[3]
    L_v_joyX = path.split(";")[4]
    L_v_joyY = path.split(";")[5]
    L_v_press = path.split(";")[6]
    
    #print("X:" + R_v_joyX + "  Y:" + R_v_joyY)
    try:
        client.write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nOK".encode("utf-8"))
    except OSError as e:
        print("OSError:", e)

@webserver.handle('/*NEW_BLOCKS')
def handle_new_blocks(client, path, request):
    try:
        files = os.listdir('/moje_bloky')
        files_without_extension = [f.split('.', 1)[0] if '.' in f else f for f in files]
        files_list = ';'.join(files_without_extension)
        client.write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n".encode("utf-8"))
        client.write(files_list.encode("utf-8"))
    except OSError as e:
        print("OSError:", e)



# handlers for filemanager
import filemanager

@webserver.handle('/fmcontents')
def _handle_contents(client, path, request):
    filemanager.handle_contents(client, path, request)

@webserver.handle('/fmupload')
def _handle_upload(client, path, request):
    filemanager.handle_upload(client, path, request)

@webserver.handle('/fmdownload')
def _handle_download(client, path, request):
    filemanager.handle_download(client, path, request)

@webserver.handle('/fmdelete')
def _handle_delete(client, path, request):
    filemanager.handle_delete(client, path, request)

@webserver.handle('/fmrename')
def _handle_rename(client, path, request):
    filemanager.handle_rename(client, path, request)

@webserver.handle('/fmnewfolder')
def _handle_newfolder(client, path, request):
    filemanager.handle_newfolder(client, path, request)

@webserver.handle('/fmmove')
def _handle_move(client, path, request):
    filemanager.handle_move(client, path, request)

@webserver.handle('/fmcopy')
def _handle_copy(client, path, request):
    filemanager.handle_copy(client, path, request)

@webserver.handle('/fmstatus')
def _handle_status(client, path, request):
    filemanager.handle_status(client, path, request)



webserver.start()

gc.collect()

# Start FTP serveru
import uftpd

gc.collect()


print("Inicializace desky dokoncena")
fbuf.text("Inicializace OK", 5, 56, 1)


if display_connected == True:
    display.show()


# Autostart programu
try:
    start_data = open("idecode").read(16)
    if "#autostart*" in start_data:
        print("Autostart programu za 3s")
        time.sleep(1)
        
        fbuf.fill(0)
        fbuf.text("Startuji program", 0, 30, 1)
        
        if display_connected == True:
            display.show()
            
        time.sleep(2)
        print("Startuji...")
        run_code()
except:
    time.sleep_ms(0)


