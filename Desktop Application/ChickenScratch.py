import time
import zroya #For Desktop Notifications
import tkinter as tk #For drawing a window
import pyperclip as pc # For copying text to the clipboard
from infi.systray import SysTrayIcon #For creating a system tray icon
import bluetooth
import os

#Define the icon path
icon_path = os.path.join(os.getcwd(), "chickenscratch.ico")
app_name = "ChickenScratch"

#define global space vars
text_list = []
button_list = []
window = None
systray = None


def quit_app(sys):
    print("Destroy Window")
    window.destroy()

def show_window(sys):
    print("Show Window")
    window.deiconify()

def hide_window():
    print("Hide Window")
    window.withdraw()
    pass
    

#First create our system tray icon
def create_systray():
    menu_options = (("Open", None, show_window),)
    systray = SysTrayIcon(icon_path, app_name, menu_options, on_quit=quit_app)
    systray.start()
    return systray

#Create our window
def create_window():
    window = tk.Tk()
    window.title(app_name)
    window.iconbitmap(icon_path)
    return window

#Pack window based on text list
def create_window_buttons():
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
    return b_list

#Add to text buffer
def add_to_text_list(text):
    for b in button_list:
        b.pack_forget()
    text_list.append(text)
    return create_window_buttons()

#Setup Bluetooth connections
def find_bluetooth_devices():
    nearby_devices = bluetooth.discover_devices(lookup_names=True)
    print("Found {} devices.".format(len(nearby_devices)))

    for addr, name in nearby_devices:
        print("  {} - {}".format(addr, name))

#

systray = create_systray()
window = create_window()
window.protocol("WM_DELETE_WINDOW", hide_window)
window.withdraw()
button_list = add_to_text_list("Hello World")
button_list = add_to_text_list("Goodbye Shelia")
button_list = add_to_text_list("Beep Boop Test")

find_bluetooth_devices()

window.mainloop()
