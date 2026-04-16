import tkinter as tk
import ctypes
import game_home_page
import new_account_page
import pygame
import os

ctypes.windll.shcore.SetProcessDpiAwareness(1)

pygame.mixer.init()

def play_sound(file):
    base = os.path.dirname(__file__)
    path = os.path.join(base, file)
    pygame.mixer.Sound(path).play()

def submit():
    play_sound("click.mp3")

    user = username.get()
    pwd = password.get()

    try:
        with open("users.txt", "r") as f:
            data = f.readlines()
    except:
        data = []

    for line in data:
        u, p = line.strip().split(",")
        if u == user and p == pwd:
            root.withdraw()
            game_home_page.open_window(root, user)
            return

    status.config(text="Invalid Login!", fg="red")

def new_account():
    play_sound("click.mp3")
    root.withdraw()
    new_account_page.open_window(root)

root = tk.Tk()
root.title("Word Scramble")
root.geometry("800x600")
root.config(bg="#020617")

tk.Label(root, text="WORD SCRAMBLE", font=("Segoe UI", 30, "bold"),
         fg="#38bdf8", bg="#020617").pack(pady=30)

frame = tk.Frame(root, bg="#0f172a", padx=40, pady=40)
frame.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(frame, text="Login", font=("Segoe UI", 20, "bold"),
         fg="white", bg="#0f172a").pack(pady=10)

tk.Label(frame, text="Username", fg="#94a3b8", bg="#0f172a").pack(anchor="w")
username = tk.Entry(frame, font=("Segoe UI", 14), width=25)
username.pack(pady=8)

tk.Label(frame, text="Password", fg="#94a3b8", bg="#0f172a").pack(anchor="w")
password = tk.Entry(frame, show="*", font=("Segoe UI", 14), width=25)
password.pack(pady=8)

status = tk.Label(frame, bg="#0f172a")
status.pack()

tk.Button(frame, text="PLAY", command=submit,
          bg="#38bdf8", fg="black",
          font=("Segoe UI", 14, "bold")).pack(pady=15)

tk.Button(frame, text="Create Account", command=new_account,
          bg="#0f172a", fg="#38bdf8", border=0).pack()

root.mainloop()