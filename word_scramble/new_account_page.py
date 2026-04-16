import tkinter as tk
import pygame
import os

def play_sound(file):
    base = os.path.dirname(__file__)
    path = os.path.join(base, file)
    pygame.mixer.Sound(path).play()

def open_window(parent):
    root = tk.Toplevel(parent)
    root.geometry("800x600")
    root.title("Create Account")
    root.config(bg="#020617")

    frame = tk.Frame(root, bg="#0f172a", padx=40, pady=40)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    # 🔷 Title
    tk.Label(frame, text="Create Account",
             font=("Segoe UI", 20, "bold"),
             fg="white", bg="#0f172a").pack(pady=15)

    # 🔷 Username
    tk.Label(frame, text="Username",
             fg="#94a3b8", bg="#0f172a").pack(anchor="w")
    user = tk.Entry(frame, font=("Segoe UI", 12), width=25)
    user.pack(pady=8)

    # 🔷 Password
    tk.Label(frame, text="Password",
             fg="#94a3b8", bg="#0f172a").pack(anchor="w")
    pwd = tk.Entry(frame, show="*", font=("Segoe UI", 12), width=25)
    pwd.pack(pady=8)

    # 🔷 Confirm Password
    tk.Label(frame, text="Confirm Password",
             fg="#94a3b8", bg="#0f172a").pack(anchor="w")
    confirm = tk.Entry(frame, show="*", font=("Segoe UI", 12), width=25)
    confirm.pack(pady=8)

    # 🔷 Status message
    status = tk.Label(frame, text="", bg="#0f172a", font=("Segoe UI", 11))
    status.pack(pady=10)

    # 🔥 Create account logic
    def create():
        play_sound("click.mp3")

        if user.get() == "" or pwd.get() == "" or confirm.get() == "":
            status.config(text="All fields are required", fg="red")
            return

        if pwd.get() != confirm.get():
            status.config(text="Passwords do not match", fg="red")
            return

        with open("users.txt", "a") as f:
            f.write(f"{user.get()},{pwd.get()}\n")

        status.config(text="Account Created Successfully!", fg="green")

        # Optional: clear fields
        user.delete(0, tk.END)
        pwd.delete(0, tk.END)
        confirm.delete(0, tk.END)

    # 🔷 Buttons
    tk.Button(frame, text="Create Account",
              command=create,
              bg="#38bdf8", fg="black",
              font=("Segoe UI", 12, "bold"),
              width=20).pack(pady=10)

    tk.Button(root, text="Back",
              command=lambda: [root.destroy(), parent.deiconify()],
              bg="#ef4444", fg="white",
              font=("Segoe UI", 11)).pack(pady=15)