"""
JARVIS - Voice Assistant
========================
Requirements:
    pip install speechrecognition pyttsx3 pyaudio wikipedia requests

On Linux you may also need:
    sudo apt-get install portaudio19-dev python3-pyaudio espeak

Usage:
    python jarvis.py

Wake word: "jarvis"
Say "exit" or "quit" or "goodbye" to stop.
"""

import os
import sys
import time
import datetime
import webbrowser
import subprocess
import threading
import platform
import urllib.parse

try:
    import speech_recognition as sr
except ImportError:
    print("[ERROR] speechrecognition not installed. Run: pip install speechrecognition")
    sys.exit(1)

try:
    import pyttsx3
except ImportError:
    print("[ERROR] pyttsx3 not installed. Run: pip install pyttsx3")
    sys.exit(1)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
WAKE_WORD       = "jarvis"
VOICE_RATE      = 175          # words per minute
VOICE_VOLUME    = 1.0          # 0.0 – 1.0
# Set preferred voice index (0 = first available). Try 1 for a different voice.
PREFERRED_VOICE_INDEX = 0
LISTEN_TIMEOUT  = 6            # seconds to wait for speech
PHRASE_LIMIT    = 8            # max seconds per phrase
AMBIENT_DURATION = 1           # seconds to calibrate mic noise

# ─────────────────────────────────────────────
# APP DEFINITIONS  (name → executable / path)
# ─────────────────────────────────────────────
SYSTEM = platform.system()  # "Windows" | "Darwin" | "Linux"

APPS = {
    # Browsers
    "chrome":       {"win": "chrome",          "mac": "open -a 'Google Chrome'",   "linux": "google-chrome"},
    "firefox":      {"win": "firefox",          "mac": "open -a Firefox",           "linux": "firefox"},
    "edge":         {"win": "msedge",           "mac": "open -a 'Microsoft Edge'",  "linux": "microsoft-edge"},

    # Productivity
    "notepad":      {"win": "notepad",          "mac": "open -a TextEdit",          "linux": "gedit"},
    "calculator":   {"win": "calc",             "mac": "open -a Calculator",        "linux": "gnome-calculator"},
    "calendar":     {"win": "outlookcal:",      "mac": "open -a Calendar",          "linux": "gnome-calendar"},
    "files":        {"win": "explorer",         "mac": "open ~",                    "linux": "nautilus"},
    "terminal":     {"win": "cmd",              "mac": "open -a Terminal",          "linux": "gnome-terminal"},

    # Media
    "spotify":      {"win": "spotify",          "mac": "open -a Spotify",           "linux": "spotify"},
    "vlc":          {"win": "vlc",              "mac": "open -a VLC",               "linux": "vlc"},
    "music":        {"win": "mswindowsmusic:",  "mac": "open -a Music",             "linux": "rhythmbox"},

    # Communication
    "whatsapp":     {"win": "whatsapp:",        "mac": "open -a WhatsApp",          "linux": "whatsapp-desktop"},
    "telegram":     {"win": "telegram",         "mac": "open -a Telegram",          "linux": "telegram-desktop"},
    "discord":      {"win": "discord",          "mac": "open -a Discord",           "linux": "discord"},
    "slack":        {"win": "slack",            "mac": "open -a Slack",             "linux": "slack"},
    "zoom":         {"win": "zoom",             "mac": "open -a zoom.us",           "linux": "zoom"},

    # Office
    "word":         {"win": "winword",          "mac": "open -a 'Microsoft Word'",  "linux": "libreoffice --writer"},
    "excel":        {"win": "excel",            "mac": "open -a 'Microsoft Excel'", "linux": "libreoffice --calc"},
    "powerpoint":   {"win": "powerpnt",         "mac": "open -a 'Microsoft PowerPoint'", "linux": "libreoffice --impress"},

    # System
    "settings":     {"win": "ms-settings:",    "mac": "open -a 'System Preferences'", "linux": "gnome-control-center"},
    "task manager": {"win": "taskmgr",          "mac": "open -a 'Activity Monitor'",   "linux": "gnome-system-monitor"},
    "paint":        {"win": "mspaint",          "mac": "open -a Preview",              "linux": "gimp"},
    "camera":       {"win": "microsoft.windows.camera:", "mac": "open -a Photo Booth", "linux": "cheese"},

    # Web shortcuts
    "youtube":      {"win": None, "mac": None, "linux": None, "url": "https://youtube.com"},
    "gmail":        {"win": None, "mac": None, "linux": None, "url": "https://mail.google.com"},
    "google":       {"win": None, "mac": None, "linux": None, "url": "https://google.com"},
    "github":       {"win": None, "mac": None, "linux": None, "url": "https://github.com"},
    "netflix":      {"win": None, "mac": None, "linux": None, "url": "https://netflix.com"},
    "amazon":       {"win": None, "mac": None, "linux": None, "url": "https://amazon.com"},
    "twitter":      {"win": None, "mac": None, "linux": None, "url": "https://twitter.com"},
    "instagram":    {"win": None, "mac": None, "linux": None, "url": "https://instagram.com"},
    "reddit":       {"win": None, "mac": None, "linux": None, "url": "https://reddit.com"},
    "wikipedia":    {"win": None, "mac": None, "linux": None, "url": "https://wikipedia.org"},
    "maps":         {"win": None, "mac": None, "linux": None, "url": "https://maps.google.com"},
}

# ─────────────────────────────────────────────
# TTS ENGINE
# ─────────────────────────────────────────────
class Speaker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', VOICE_RATE)
        self.engine.setProperty('volume', VOICE_VOLUME)

        voices = self.engine.getProperty('voices')
        if voices:
            idx = min(PREFERRED_VOICE_INDEX, len(voices) - 1)
            self.engine.setProperty('voice', voices[idx].id)
            print(f"[Voice] Using: {voices[idx].name}")

        self._lock = threading.Lock()

    def say(self, text: str):
        print(f"[JARVIS] {text}")
        with self._lock:
            self.engine.say(text)
            self.engine.runAndWait()

# ─────────────────────────────────────────────
# LISTENER
# ─────────────────────────────────────────────
class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.mic = sr.Microphone()

    def calibrate(self):
        print("[Mic] Calibrating for ambient noise...")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=AMBIENT_DURATION)
        print("[Mic] Ready.")

    def listen(self) -> str | None:
        with self.mic as source:
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=LISTEN_TIMEOUT,
                    phrase_time_limit=PHRASE_LIMIT
                )
            except sr.WaitTimeoutError:
                return None

        try:
            text = self.recognizer.recognize_google(audio).lower().strip()
            print(f"[Heard] {text}")
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[SR Error] {e}")
            return None

# ─────────────────────────────────────────────
# COMMAND HANDLER
# ─────────────────────────────────────────────
class Jarvis:
    def __init__(self):
        self.speaker  = Speaker()
        self.listener = Listener()
        self.running  = False

    # ── helpers ───────────────────────────────
    def _open_app(self, name: str) -> bool:
        app = APPS.get(name)
        if not app:
            return False

        # URL-only entries
        if app.get("url"):
            webbrowser.open(app["url"])
            return True

        key = {"Windows": "win", "Darwin": "mac", "Linux": "linux"}.get(SYSTEM, "linux")
        cmd = app.get(key)

        if not cmd:
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(name)}")
            return True

        try:
            if SYSTEM == "Windows":
                os.startfile(cmd) if ":" in cmd else subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            print(f"[App Error] {e}")
            return False

    def _web_search(self, query: str):
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)

    def _youtube_search(self, query: str):
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)

    def _get_time(self) -> str:
        now = datetime.datetime.now()
        return now.strftime("%-I:%M %p").lstrip("0") if SYSTEM != "Windows" else now.strftime("%I:%M %p").lstrip("0")

    def _get_date(self) -> str:
        return datetime.datetime.now().strftime("%A, %B %d, %Y")

    # ── command router ────────────────────────
    def handle(self, text: str) -> bool:
        """
        Returns True to keep running, False to exit.
        """
        t = text.strip().lower()

        # ── EXIT ──────────────────────────────
        if any(w in t for w in ("exit", "quit", "goodbye", "shut down", "shutdown", "bye")):
            self.speaker.say("Goodbye! Have a great day.")
            return False

        # ── GREETINGS ─────────────────────────
        if any(w in t for w in ("hello", "hi jarvis", "hey jarvis", "how are you")):
            self.speaker.say("Hello! I'm Jarvis, fully operational. How can I help?")
            return True

        # ── TIME ──────────────────────────────
        if "time" in t:
            self.speaker.say(f"The current time is {self._get_time()}.")
            return True

        # ── DATE ──────────────────────────────
        if "date" in t or "today" in t:
            self.speaker.say(f"Today is {self._get_date()}.")
            return True

        # ── OPEN APP / WEBSITE ────────────────
        if t.startswith("open "):
            target = t[5:].strip()
            if self._open_app(target):
                self.speaker.say(f"Opening {target}.")
            else:
                # Try fuzzy match
                for app_name in APPS:
                    if app_name in target or target in app_name:
                        self._open_app(app_name)
                        self.speaker.say(f"Opening {app_name}.")
                        return True
                self.speaker.say(f"I couldn't find {target}. Searching the web instead.")
                self._web_search(target)
            return True

        # ── WEB SEARCH ────────────────────────
        for prefix in ("search for", "search", "google", "look up", "find"):
            if t.startswith(prefix + " "):
                query = t[len(prefix):].strip()
                self.speaker.say(f"Searching for {query}.")
                self._web_search(query)
                return True

        # ── YOUTUBE ───────────────────────────
        for prefix in ("play", "youtube", "watch"):
            if t.startswith(prefix + " "):
                query = t[len(prefix):].strip()
                self.speaker.say(f"Playing {query} on YouTube.")
                self._youtube_search(query)
                return True

        # ── WIKIPEDIA ─────────────────────────
        for prefix in ("wikipedia", "wiki", "tell me about", "what is", "who is"):
            if t.startswith(prefix + " "):
                query = t[len(prefix):].strip()
                self.speaker.say(f"Looking up {query} on Wikipedia.")
                url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query.replace(' ', '_'))}"
                webbrowser.open(url)
                return True

        # ── MAPS ──────────────────────────────
        for prefix in ("directions to", "navigate to", "take me to", "how to get to"):
            if t.startswith(prefix + " "):
                place = t[len(prefix):].strip()
                self.speaker.say(f"Getting directions to {place}.")
                webbrowser.open(f"https://maps.google.com/maps?q={urllib.parse.quote(place)}")
                return True

        # ── WEATHER ───────────────────────────
        if "weather" in t:
            city = t.replace("weather in", "").replace("weather for", "").replace("weather", "").strip() or "current location"
            self.speaker.say(f"Checking weather for {city}.")
            webbrowser.open(f"https://www.google.com/search?q=weather+{urllib.parse.quote(city)}")
            return True

        # ── NEWS ──────────────────────────────
        if "news" in t:
            topic = t.replace("latest news about", "").replace("news about", "").replace("news", "").strip()
            self.speaker.say(f"Fetching the latest news{' about ' + topic if topic else ''}.")
            webbrowser.open(f"https://news.google.com/search?q={urllib.parse.quote(topic)}" if topic else "https://news.google.com")
            return True

        # ── SCREENSHOT ────────────────────────
        if "screenshot" in t:
            self.speaker.say("Taking a screenshot.")
            if SYSTEM == "Windows":
                subprocess.Popen("snippingtool", shell=True)
            elif SYSTEM == "Darwin":
                subprocess.Popen("screencapture -i ~/Desktop/screenshot.png", shell=True)
            else:
                subprocess.Popen("gnome-screenshot -i", shell=True)
            return True

        # ── VOLUME ────────────────────────────
        if "volume up" in t or "increase volume" in t:
            self.speaker.say("Turning volume up.")
            if SYSTEM == "Windows":   subprocess.Popen("nircmd.exe changesysvolume 5000", shell=True)
            elif SYSTEM == "Darwin":  subprocess.Popen("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'", shell=True)
            else:                     subprocess.Popen("amixer -D pulse sset Master 10%+", shell=True)
            return True

        if "volume down" in t or "decrease volume" in t or "lower volume" in t:
            self.speaker.say("Turning volume down.")
            if SYSTEM == "Windows":   subprocess.Popen("nircmd.exe changesysvolume -5000", shell=True)
            elif SYSTEM == "Darwin":  subprocess.Popen("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'", shell=True)
            else:                     subprocess.Popen("amixer -D pulse sset Master 10%-", shell=True)
            return True

        if "mute" in t:
            self.speaker.say("Muting.")
            if SYSTEM == "Windows":   subprocess.Popen("nircmd.exe mutesysvolume 1", shell=True)
            elif SYSTEM == "Darwin":  subprocess.Popen("osascript -e 'set volume with output muted'", shell=True)
            else:                     subprocess.Popen("amixer -D pulse sset Master mute", shell=True)
            return True

        # ── JOKES ─────────────────────────────
        if "joke" in t or "make me laugh" in t:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything.",
                "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "I'm reading a book about anti-gravity. It's impossible to put down.",
            ]
            import random
            self.speaker.say(random.choice(jokes))
            return True

        # ── HELP ──────────────────────────────
        if "help" in t or "what can you do" in t or "commands" in t:
            self.speaker.say(
                "I can open apps like Chrome, Spotify, or Notepad. "
                "Search the web, YouTube, or Wikipedia. "
                "Tell you the time and date. Get directions, weather, or news. "
                "Control your volume. And tell jokes. Just say Jarvis followed by your command."
            )
            return True

        # ── UNKNOWN ───────────────────────────
        self.speaker.say(f"I'm not sure how to handle that. Let me search it for you.")
        self._web_search(t)
        return True

    # ── main loop ─────────────────────────────
    def run(self):
        self.listener.calibrate()
        self.speaker.say("Jarvis online. Say 'Jarvis' followed by your command.")
        self.running = True

        print(f"\n{'─'*50}")
        print(f"  JARVIS  |  Wake word: '{WAKE_WORD}'")
        print(f"  Say '{WAKE_WORD} help' for a list of commands.")
        print(f"  Say 'exit' or 'goodbye' to quit.")
        print(f"{'─'*50}\n")

        while self.running:
            print("[Listening for wake word...]")
            text = self.listener.listen()

            if not text:
                continue

            # Check for wake word
            if WAKE_WORD not in text:
                continue

            # Strip wake word prefix
            command = text.replace(WAKE_WORD, "").strip(" ,.")
            if not command:
                self.speaker.say("Yes? How can I help?")
                print("[Listening for command...]")
                command = self.listener.listen() or ""
                if not command:
                    self.speaker.say("I didn't catch that. Please try again.")
                    continue

            self.running = self.handle(command)

        print("[JARVIS] Shutting down.")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    jarvis = Jarvis()
    try:
        jarvis.run()
    except KeyboardInterrupt:
        print("\n[Interrupted] Shutting down Jarvis.")
        jarvis.speaker.say("Shutting down. Goodbye.")
