import time
import zroya #For Desktop Notifications
import tkinter as tk #For drawing a window
import pyperclip as pc # For copying text to the clipboard
from infi.systray import SysTrayIcon #For creating a system tray icon
import os
import serial
import serial.tools.list_ports
import io
import collections


#################################################################################
########################### GLOBAL VARIABLES ####################################
#################################################################################
icon_path = os.path.join(os.getcwd(), "chickenscratch.ico")
app_name = "ChickenScratch"

text_list = collections.deque(maxlen=8)
button_list = []
window = None
systray = None
ser = None

#################################################################################
########################### WINDOW EXPRESSIONS ##################################
#################################################################################

def quit_app(sys):
    global window
    print("Destroy Window")
    window.destroy()

def show_window(sys):
    global window
    print("Show Window")
    window.deiconify()

def hide_window():
    global window
    print("Hide Window")
    window.withdraw()
    pass

#################################################################################
########################### SERIAL PORT HANDLING ################################
#################################################################################

# Open a serial port
def open_serial_listener(port):
    global ser
    ser = serial.Serial(port, timeout=0)
    print("Connected")

# Close a serial port
def close_serial_listener():
    global ser
    ser.close()

#################################################################################
########################### SERIAL PORT MONITORING ##############################
#################################################################################

def serial_listen_loop():
    global ser
    if ser == None:
        window.after(1000, serial_listen_loop)
        return

    global button_list
    text = ser.readline()
    st = text.decode()
    if not st == '':
        print ("Adding " + st)
        button_list = add_to_text_list(st)
    window.after(1000, serial_listen_loop)

#################################################################################
########################### SYSTRAY HANDLING ####################################
#################################################################################

# Create a System Tray Icon
def create_systray(ports):

    submenus = []
    for port, desc, hwid in sorted(ports):
        print(port)
        sub = (str(port) + ": " + str(desc), None, lambda x, p=port: open_serial_listener(p),)
        submenus.append(sub)
    
    menu_options = (
                    ("Open", None, show_window),
                    ("Ports", None, tuple(submenus)),
                    )
    systray = SysTrayIcon(icon_path, app_name, menu_options, on_quit=quit_app)
    systray.start()
    return systray


#################################################################################
########################### WINDOW HANDLING #####################################
#################################################################################

# Create a window
def create_window():
    window = tk.Tk()
    window.title(app_name)
    window.iconbitmap(icon_path)
    return window

#Pack window based on text list
def create_window_buttons():
    global window
    b_list = []
    for t in text_list:
        button = tk.Button(
            text=t,
            width=40,
            height=5,
            command= lambda lt = t: pc.copy(lt)
        )
        button.pack()
        b_list.append(button)
    window.update()
    return b_list

#################################################################################
########################### WINDOW UPDATING #####################################
#################################################################################

# Add text to the text list and update windows
def add_to_text_list(text):
    for b in button_list:
        b.pack_forget()
    text_list.append(text)
    return create_window_buttons()


#################################################################################
########################### CORE LOGIC  #########################################
#################################################################################

# Create the systray icon
ports = serial.tools.list_ports.comports()
systray = create_systray(ports)

# Create the window
window = create_window()
window.protocol("WM_DELETE_WINDOW", hide_window)
window.withdraw()

# Initialize serial loop
window.after(250, serial_listen_loop)

window.mainloop()
