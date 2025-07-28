import os
import speech_recognition as sr
import subprocess
import sys
import asyncio
from TTS.api import TTS
import sounddevice as sd
from threading import Thread
from googletrans import Translator
import builtins
import requests
import functools
import fasttext
import dateparser
import spacy
import re
from datetime import datetime, timedelta
from tzlocal import get_localzone_name
from dateparser.search import search_dates
import sqlite3
import datetime
import os.path
import feedparser
import webbrowser
import json
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
print = functools.partial(builtins.print, flush=True)
tts = None
TTS_READY = 0
fastmodel = None
my_lang = {
        "to Arabic": "ar",
        "to Chinese": "zh-CN",
        "to Dutch": "nl",
        "to English": "en",
        "to French": "fr",
        "to German": "de",
        "to Hindi": "hi",
        "to Italian": "it",
        "to Japanese": "ja",
        "to Korean": "ko",
        "to Persian": "fa",
        "to Polish": "pl",
        "to Portuguese": "pt",
        "to Russian": "ru",
        "to Spanish": "es",
        "to Turkish": "tr",
        "to Ukrainian": "uk",
        "to Urdu": "ur",
        "to Vietnamese": "vi"
        }
def excel():
        os.system("start excel.exe")

def internet():
        os.system("start chrome.exe")

def media():
        os.system("start wmplayer.exe")

def respond_voice(text, language="en"):
        #subprocess.run(["espeak", text])
        print("Loading response voice")
        speaker = tts.speakers[0]
        wav = tts.tts(text, language=language, speaker=speaker)
        sample_rate = tts.synthesizer.output_sample_rate
        sd.play(wav, sample_rate)
        sd.wait()
        print("Response done: You can speak now")

def AI(user):
        result = subprocess.run(
                ["ollama", "run", "gemma:2b", user],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                encoding="utf-8"
        )
        return result.stdout.strip()
async def translate_text(text, src_lang='en', dest_lang='fr'):
        translator = Translator()
        result = await translator.translate(text, src=src_lang, dest=dest_lang)
        return result.text         

def translate_t(user):
        user = user[len("translate"):].lstrip()
        dest_lang = ""
        lang_found = 0
        for key in my_lang:
                if user.endswith(key):
                        user = user[:-len(key)].rstrip()
                        dest_lang = my_lang[key]
                        lang_found = 1
        if lang_found == 0:
                print("I don't know your language, default translate to english")
                dest_lang = 'en'
        #src_lang = detect(user)
        labels, probs = fastmodel.predict(user)
        src_lang = labels[0].replace('__label__', '')
        result_text = asyncio.run(translate_text(user, src_lang, dest_lang))
        print(result_text)
        respond_voice(result_text, dest_lang)

class updatedSchedule:
        def __init__(self, start, duration=30, subject="Team Meeting", location="Conference Room", body="Discuss Q3 progress."):
                if start:
                        self.start = start
                else:
                        self.start = datetime(2025, 7, 28, 17, 0)
                self.duration = duration
                self.subject = subject
                self.location = location
                self.body = body

        def __str__(self):
                return "Start: " + self.start.strftime("%Y-%m-%d %H:%M:%S") + " Duration: " + str(self.duration) + " Subject: " + self.subject + " Location: " + self.location + " Body: " + self.body

def extract_subject_spacy(fultext, nlp):
        text = fultext.lower()
        text = re.sub(
                r"^(schedule|set|create|arrange|organize|make)\s+(a\s+)?(meeting|appointment|event)\s*(for|to)?\s*", "",
                text, flags=re.IGNORECASE)

        # Remove date/time/duration phrases using regex
        text = re.sub(r"\b(on|at|by|for|in|around|from|to|until|next)\b.*", "", text)
        doc = nlp(text)
        subject_tokens = []
        for token in doc:
                if token.is_punct or token.is_space:
                        continue
                subject_tokens.append(token.text)

        subject = " ".join(subject_tokens).strip()
        if not subject:
                return "Meeting"
        return subject[0].upper() + subject[1:]

DURATION_KEYWORDS = ["for", "lasting", "during", "about"]
TIME_INDICATORS = ["am", "pm", "o'clock", "morning", "evening", "noon", "midnight"]

def is_datetime(phrase):
        dt = dateparser.parse(phrase)
        return dt is not None

def clean_location_phrase(phrase):
        # Remove leading prepositions
        phrase = re.sub(r"^(at|in|on)\s+", "", phrase, flags=re.IGNORECASE)
        # Remove trailing duration phrases
        for kw in DURATION_KEYWORDS:
                phrase = re.sub(rf"\b{kw}\b.*", "", phrase, flags=re.IGNORECASE).strip()
        return phrase.strip()

def extract_location(text, nlp):
        doc = nlp(text)
        location_candidates = []

        for i, token in enumerate(doc):
                if token.lower_ in ["at", "in"]:  # <-- remove 'on' here
                        phrase_tokens = []
                        for t in doc[i + 1:i + 10]:
                                if t.lower_ in DURATION_KEYWORDS or any(
                                        ind in t.text.lower() for ind in TIME_INDICATORS):
                                        break
                                phrase_tokens.append(t.text)
                        phrase = " ".join(phrase_tokens).strip()
                        if phrase and not is_datetime(phrase):
                                location_candidates.append(phrase)
        # Fallback to named entities
        for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC", "FAC", "ORG"]:
                        # Filter out dates and times
                        if not is_datetime(ent.text):
                                location_candidates.append(ent.text)

                # Return first suitable candidate
        for loc in location_candidates:
                if loc:
                        return loc

        return "No Location"

def extractSchedule(text):
        nlp = spacy.load("en_core_web_sm")
        #dateTime = dateparser.parse(text)
        dateTime = search_dates(text)[0][1]
        doc = nlp(text)
        duration = 30
        duration_match = re.search(r'for (\d+\.?\d*) ?(minutes?|hours?)', text, re.IGNORECASE)
        if duration_match:
                number = float(duration_match.group(1))
                unit = duration_match.group(2).lower()
                if "hour" in unit:
                        minutes = int(number * 60)
                else:
                        minutes = int(number)
                duration = minutes
        location = extract_location(text, nlp)
        subject = extract_subject_spacy(text, nlp)
        body = ""
        return updatedSchedule(dateTime, duration, subject, location, body)

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def loadCred():
        creds = None
        token_file = 'token.json'

        # Load existing credentials
        if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # If there are no valid credentials, go through the OAuth flow
        if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                else:
                        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                        creds = flow.run_local_server(port=0)
                # Save the credentials to token.json
                with open(token_file, 'w') as token:
                        token.write(creds.to_json())
        return creds
new_creds = None
def schedule(text):
        #flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        #creds = flow.run_local_server(port=0)
        creds = new_creds
        sch = extractSchedule(text)
        print(sch)
        service = build('calendar', 'v3', credentials=creds)
        end = sch.start + timedelta(minutes=sch.duration)
        timez = get_localzone_name()
        # 🗓️ Define the event
        event = {
                'summary': sch.subject,
                'location': sch.location,
                'description': sch.body,
                'start': {
                        'dateTime': sch.start.isoformat(),
                        'timeZone': timez,
                },
                'end': {
                        'dateTime': end.isoformat(),
                        'timeZone': timez,
                },
                'reminders': {
                        'useDefault': True,
                },
        }

        event_result = service.events().insert(calendarId='primary', body=event).execute()

def Cancelschedule(text):
        #flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        #creds = flow.run_local_server(port=0)
        creds = new_creds
        service = build('calendar', 'v3', credentials=creds)
        dateTime = search_dates(text)[0][1]
        now = dateTime.isoformat() + 'Z'
        events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
        ).execute()
        event_id = ""

        events = events_result.get('items', [])
        nlp = spacy.load("en_core_web_sm")
        subject = extract_subject_spacy(text, nlp)
        for event in events:
                if event['start'].get('dateTime').startswith(dateTime.isoformat()):
                        event_id = event['id']
                        break
                if event['summary'] == subject:
                        event_id = event['id']
                        break
                #print(event['id'], event['summary'], event['start'].get('dateTime'))
        # Assume 'creds' is your authenticated Credentials object
        service = build('calendar', 'v3', credentials=creds)

        calendar_id = 'primary'
        try:
                service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                print("✅ Event deleted successfully.")
        except Exception as e:
                print(f"Error deleting event: {e}")

conn = None
cursor = None
DB_NAME = "todo.db"
def setup_db():
        # Initialize SQLite DB
        global conn, cursor
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                done INTEGER DEFAULT 0
                )
        """)
        conn.commit()
        conn.close()
# Add task
def add_task(description):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
                cursor.execute("INSERT INTO tasks (description) VALUES (?)", (description,))
                conn.commit()
                print(f"✅ Task added: '{description}'")
        except sqlite3.IntegrityError:
                print(f"Task '{description}' already exists.")
        conn.close()


# List tasks
def list_tasks():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT description, done FROM tasks")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
                print("Your list is empty.")
                return
        print("\n".join([f"[{'✓' if done else '✗'}] {desc}" for desc, done in rows]))


# Mark task as done
def mark_done(description):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET done = 1 WHERE description = ?", (description,))
        if cursor.rowcount == 0:
                conn.close()
                print(f"Task '{description}' not found.")
                return
        conn.commit()
        conn.close()
        print(f"☑️ Task {description} marked as done.")

# Delete task
def delete_task(description):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE description = ?", (description,))
        if cursor.rowcount == 0:
                conn.close()
                print(f"Task '{description}' not found.")
                return
        conn.commit()
        conn.close()
        print(f"🗑️ Task {description} deleted.")

def get_city_by_ip():
    response = requests.get("https://ipinfo.io/json")
    if response.status_code == 200:
        data = response.json()
        return data.get("city")
    return ""

def getweather():
        load_dotenv()  # This loads variables from .env into os.environ
        api_key = os.getenv("WEATHER_API_KEY")
        city = get_city_by_ip()
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        response = requests.get(url)
        weather = {}
        if response.status_code == 200:
                data = response.json()
                weather = {
                        'city': data['name'],
                        'temperature': data['main']['temp'],
                        'description': data['weather'][0]['description'],
                        'humidity': data['main']['humidity'],
                        'wind_speed': data['wind']['speed']
                }
                print(weather.get('city') + " has " + weather.get('description') + " with a temperature of " + str(weather.get('temperature')) + " degrees celsius with a humidity of " + str(weather.get('humidity')) + " and a wind speed of " + str(weather.get('wind_speed')) + ".")
                return
        print("Weather is not available.")

def getnews():
        feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
        news_list = []
        for entry in feed.entries[:3]:  # Top 3 articles
                news_list.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": entry.summary
                })
        for i in news_list:
                print("News Title: " + i.get('title') + "\nSummary: " + i.get('summary'))

def get_today_events():
        creds = new_creds
        service = build('calendar', 'v3', credentials=creds)
        # Get the current time range for "today"
        now = datetime.datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'

        events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
                print("No events today.")
        else:
                print("Today's events:")
                for event in events:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        print(f"🕒 {start} — {event['summary']}")


def overview():
        get_today_events()
        list_tasks()
        getweather()
        getnews()

def openApp(message):
        match = re.search(r'^open\s+(.+)$', message.strip(), re.IGNORECASE)
        if match:
                app_name = match.group(1).strip()
                os.system("start " + app_name + ".exe")

def playmedia(message):
        match = re.search(r"play\s+(.*)", message, re.IGNORECASE)
        if match:
                query = match.group(1).strip()
                # Add "music playlist" if not already included
                if "music" not in query.lower():
                        query += " music playlist"
                search_query = query
        else:
                search_query = "relaxing music playlist"
        result = subprocess.run([
                "yt-dlp",
                f"ytsearch1:{search_query}",
                "--dump-json"
        ], stdout=subprocess.PIPE, text=True)
        url = ""
        if result.returncode == 0:
                video_data = json.loads(result.stdout)
                url = video_data.get("webpage_url")
        else:
                url = ""
        if url == "":
                print("No results found.")
        else:
                webbrowser.open(url)
                print(f"🎵 Now playing: {search_query.title()} on YouTube")

def mainfunction(source):
        r.adjust_for_ambient_noise(source, duration=1)
        #r.pause_threshold = 1.0
        audio = r.listen(source)
        user = ""
        try:
                user = r.recognize_google(audio)
                print("You said:", user)
        except sr.UnknownValueError:
                print("Sorry, I could not understand what you said.")
        except sr.RequestError as e:
                print(f"API error: {e}")
        lower_user = user.lower()
        if user == "Excel":
                excel()
        elif user == "internet":
                internet()
        elif user == "music":
                media()
        elif user.startswith("Schedule"):
                schedule(user)
        elif user.startswith("Cancel"):
                Cancelschedule(user)
        elif lower_user.startswith("add"):
                match = re.search(r'add\s+(.+)\s+to my list', lower_user)
                if match:
                        add_task(match.group(1))
        elif "show me my list" in lower_user:
                list_tasks()
        elif lower_user.startswith("mark"):
                match = re.search(r'mark\s+(.+)\s+as done', lower_user)
                if match:
                        mark_done(match.group(1))
        elif lower_user.startswith("delete"):
                match = re.search(r'delete\s+(.+)', lower_user)
                if match:
                        delete_task(match.group(1))
        elif "weather" in lower_user:
                getweather()
        elif "news" in lower_user:
                getnews()
        elif lower_user == "give me an overview of today":
                overview()
        elif lower_user.startswith("open"):
                openApp(lower_user)
        elif lower_user.startswith("play"):
                playmedia(lower_user)
        elif user.startswith("hello AI"):
                response = AI(user[len("hello AI"):].lstrip())
                print("AI response: " + response)
                if TTS_READY == 1:
                        labels, probs = fastmodel.predict(response)
                        language = labels[0].replace('__label__', '')
                        #language = detect(response)
                        respond_voice(response, language)
        elif user == "close AI":
                os._exit(1)
        elif user.startswith("translate"):
                translate_t(user)

def background_task():
        #"tts_models/en/ljspeech/tacotron2-DDC" is the better model but slower
        global TTS_READY
        global tts
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)
        print("Loaded TTS Model")
        TTS_READY = 1
        
if __name__ == "__main__":
        print("Start of main")
        thread = Thread(target=background_task)
        thread.start()
        fastmodel = fasttext.load_model('lid.176.ftz')
        new_creds = loadCred()
        r = sr.Recognizer()
        # Extend how long it waits before assuming the user is done speaking
        r.pause_threshold = 1.5        # seconds of silence before stopping recording
        r.energy_threshold = 300       # minimum audio level to detect speech
        r.dynamic_energy_threshold = True
        CREATE_NEW_CONSOLE = 0x00000010
        p = subprocess.Popen(["python", "secondary.py"],
                                creationflags=CREATE_NEW_CONSOLE
                             )
        with sr.Microphone() as source:
                try:
                        while 1:
                                mainfunction(source)
                except BaseException as e:
                        print("Main received Ctrl+C. Killing subprocess...")
                        p.terminate()
                        p.wait()
                        print("Subprocess terminated.")
                        print("An error occured: ", repr(e))
                        sys.exit(0)
