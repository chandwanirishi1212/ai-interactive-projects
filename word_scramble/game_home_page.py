import tkinter as tk
import random as r
import pygame
import os

def play_sound(file):
    base = os.path.dirname(__file__)
    path = os.path.join(base, file)
    pygame.mixer.Sound(path).play()

def scramble(word):
    w = list(word)
    while True:
        r.shuffle(w)
        s = ''.join(w)
        if s != word:
            return s

def open_window(parent, username):
    timer_id = None
    words = [
        "python","computer","keyboard","monitor","internet","program",
        "developer","algorithm","function","variable","database","network",
        "security","software","hardware","debugging","compiler","execute",
        "syntax","object","class","inheritance","encapsulation",
        "polymorphism","abstraction","framework","library","package",
        "module","exception","iteration","condition","operator","parameter",
        "argument","constant","boolean","integer","string","float",
        "recursion","binary","decimal","encryption","firewall",
        "protocol","server","client","cloud","storage"
    ]

    points = 0
    choice = None
    time_left = 20   # 🔥 increased time

    root = tk.Toplevel(parent)
    root.geometry("800x600")
    root.config(bg="#020617")

    score_label = tk.Label(root, text="Score: 0", fg="green", bg="#020617")
    score_label.pack(anchor="ne", padx=20)

    timer_label = tk.Label(root, text="Time: 20", fg="white", bg="#020617")
    timer_label.pack()

    frame = tk.Frame(root, bg="#0f172a", padx=40, pady=40)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    label = tk.Label(frame, font=("Segoe UI", 24, "bold"),
                     fg="#38bdf8", bg="#0f172a")
    label.pack(pady=20)

    entry = tk.Entry(frame, font=("Segoe UI", 16), justify="center")
    entry.pack(pady=10)

    result = tk.Label(frame, bg="#0f172a")
    result.pack()

    def shake():
        positions = [0.52, 0.48, 0.51, 0.49, 0.5]
        for pos in positions:
            frame.place_configure(relx=pos)
            root.update()

    def countdown():
        nonlocal time_left, timer_id

        if time_left > 0:
            time_left -= 1
            timer_label.config(text=f"Time: {time_left}")
            timer_id = root.after(1000, countdown)
        else:
            play_sound("wrong.mp3")
            result.config(text=f"Time's up! {choice}", fg="red")
            next_delay()

    def next_delay():
        root.after(1200, next_word)

    def next_word():
        nonlocal choice, time_left, timer_id

        if timer_id:
            root.after_cancel(timer_id)   # 🛑 stop previous timer

        if not words:
            end_game()
            return

        time_left = 20
        timer_label.config(text="Time: 20")

        choice = r.choice(words)
        label.config(text=scramble(choice))
        entry.delete(0, tk.END)
        result.config(text="")

        countdown()

    def check():
        nonlocal points

        if entry.get().lower() == choice:
            play_sound("correct.mp3")
            points += 1
            score_label.config(text=f"Score: {points}")
            result.config(text="✔ Correct!", fg="green")
        else:
            play_sound("wrong.mp3")
            result.config(text=f"✖ Wrong! {choice}", fg="red")
            shake()

        words.remove(choice)
        next_delay()

    def end_game():
        label.config(text=f"GAME OVER\nScore: {points}")
        entry.destroy()
        submit_btn.destroy()

        with open("scores.txt", "a") as f:
            f.write(f"{username},{points}\n")

    def exit_game():
        play_sound("exit.mp3")
        root.destroy()
        parent.deiconify()

    submit_btn = tk.Button(frame, text="Submit",
                           command=check,
                           bg="#38bdf8", fg="black")
    submit_btn.pack(pady=10)

    tk.Button(root, text="EXIT",
              command=exit_game,
              bg="#ef4444", fg="white").pack(pady=10)

    next_word()