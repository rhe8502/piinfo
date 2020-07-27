#!/usr/bin/env python3

# Display-O-Tron 3000 specific libraries - Install instructions https://tinyurl.com/y653jp56
from dot3k import lcd
from dot3k import backlight
from dot3k import joystick as nav

# Python specific libraries
from gpiozero import CPUTemperature, PingServer
from time import sleep
import signal
import sys
import socket
import fcntl
import struct
import shutil
import os
import math

# Maximum Screen Count (starts at zero)
MAX_SCREENS = 3

### Custom User Settings ###

# Network Interface (e.g., eth0, wlan0, etc.)
IFACE = 'eth0'
# Mountpoint to monitor diskspace (e.g., /, /home, etc.)
DISK = '/'
# Default Gateway (Usually the IP address of your Internet router)
GATEWAY = '192.168.50.1'
# External IP address to check Internet connection (e.g., Google DNS server)
EXTIP = '8.8.8.8'


class SCRIDX:
    """ Keep track of current Screen """
    idx = 0

class BLIGHT:
    """ Keep track of Backlight Status """
    status = True

@nav.on(nav.LEFT)
def handle_left(pin):
    """ Joystick left - Switch to the previous screen """ 
    lcd.clear()

    if SCRIDX.idx > 0:
        SCRIDX.idx -=1

    screen(SCRIDX.idx)   

@nav.on(nav.RIGHT)
def handle_right(pin):
    """ Joystick right - Switch to the next screen """ 
    lcd.clear()

    if SCRIDX.idx < MAX_SCREENS:
        SCRIDX.idx +=1
    elif SCRIDX.idx == MAX_SCREENS:
        SCRIDX.idx = 0

    screen(SCRIDX.idx)    

@nav.on(nav.BUTTON)
def handle_button(pin):
    """ Joystick push - Turn Backlight ON, or OFF """     
  
    if BLIGHT.status:
        backlight.off()
        BLIGHT.status = False
    else:
        backlight.rgb(50, 255, 50)
        BLIGHT.status = True

def get_ip(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
    except IOError:
        return 'Not Found!'

def check_inet():
    """ Check Internet status """
    gw = PingServer(GATEWAY)
    inet = PingServer(EXTIP)

    if gw.is_active:
        gw_stat = 'ONLINE '
    else:
        gw_stat = 'OFFLINE'

    if inet.is_active:
        inet_stat = 'ONLINE '
        dns_stat = 'ONLINE '
        if BLIGHT.status:
            backlight.rgb(50, 255, 50)
    else:
        inet_stat = 'OFFLINE'
        dns_stat = 'OFFLINE'
        if BLIGHT.status:
            backlight.rgb(250, 120, 30)

    if  SCRIDX.idx == 3:
        lcd.set_cursor_position(0,0)
        lcd.write(f'GATEWAY :{gw_stat}')

    if  SCRIDX.idx == 3:
        lcd.set_cursor_position(0,1)
        lcd.write(f'INTERNET:{inet_stat}')
        lcd.set_cursor_position(0,2)
        lcd.write(f'DNS     :{dns_stat}')
  
def screen(scr_num):
    """ Display Rapsberry Pi Status on the LCD Screen (screen count starts at 0) """     

    if scr_num == 0:
        lcd.set_cursor_position(0,0)
        hostname=socket.gethostname()
        lcd.write(f'HOST: {hostname.upper()}')

        lcd.set_cursor_position(0,1)
        cpu = CPUTemperature()
        lcd.write(f"TEMP: {cpu.temperature:.1f}'C ")

        lcd.set_cursor_position(0,2)
        cpu=str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip())
        lcd.write(f'CPU : {cpu}%  ')
    
    elif scr_num == 1:
        lcd.set_cursor_position(0,0)
        lcd.write('IP Address:')
        lcd.set_cursor_position(0,1)
        lcd.write('----------------')
        lcd.set_cursor_position(0,2)
        lcd.write(f'{get_ip(IFACE)}')
  
    elif scr_num == 2:
        """ Determine Total/Used/Free Diskspace """
        total_ds, used_ds, free_ds = shutil.disk_usage(DISK)
        gb = 10 ** 9 # GB == gigabyte

        lcd.set_cursor_position(0,0)
        lcd.write(f'DISK: {DISK}')
        
        lcd.set_cursor_position(0,1)
        lcd.write(f'USED: {(used_ds / gb):.1f} GB')

        lcd.set_cursor_position(0,2)
        lcd.write(f'FREE: {(free_ds / gb):.1f} GB')

        """ Determine Total/Used/Free Diskspace """
        total_ds, used_ds, free_ds = shutil.disk_usage(DISK)
        gb = 10 ** 9 # GB == gigabyte

    elif scr_num == 3:
        check_inet()

def display_init():
    """ Initialize Display-O-Tron (Always a good thing to do) """
    backlight.set_graph(0) 
    lcd.set_contrast(50)
    backlight.off()
    lcd.clear()

def sig_hand(sig, frame):
    """ Ensure a clean exit with CTRL+C """
    display_init()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, sig_hand)
    display_init()
    backlight.rgb(50, 255, 50)
    
    while True:
        screen(SCRIDX.idx)
        check_inet()
        """ Refresh Raspberry Pi Status every 2 seconds. Adjust "sleep(2)" if you want a different interval """
        sleep(2)

if __name__ == "__main__":
    main()