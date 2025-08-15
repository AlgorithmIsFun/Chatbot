from __future__ import print_function
import os
import psutil
import subprocess
import sys
import asyncio
from googletrans import Translator
import builtins
import requests
import functools
import fasttext
import dateparser
import spacy
import re
from PIL import Image
from datetime import datetime, timedelta
from tzlocal import get_localzone_name
from dateparser.search import search_dates
import sqlite3
import datetime
import os.path
import feedparser
import webbrowser
import json
import threading
import time
import winsound
import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
from dotenv import load_dotenv
from ddgs import DDGS
from langdetect import detect
import trafilatura
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

print = functools.partial(builtins.print, flush=True)

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()  # Ensure immediate writing

    def flush(self):
        for f in self.files:
            f.flush()

# Open a log file
log_file = open("output.txt", "w")
sys.stdout = Tee(sys.__stdout__, log_file)
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
        lang_found = 0
        dest_lang = ""
        for key in my_lang:
                if user.endswith(key):
                        user = user[:-len(key)].rstrip()
                        dest_lang = my_lang[key]
                        lang_found = 1
        if lang_found == 0:
                print("I don't know your language, default translate to english")
                dest_lang = 'en'
        #src_lang = detect(user)
        #numpy library must be 1.26.4
        labels, probs = fastmodel.predict(user)
        src_lang = labels[0].replace('__label__', '')
        result_text = asyncio.run(translate_text(user, src_lang, dest_lang))
        print(result_text)

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
                        try:
                                creds.refresh(Request())
                        except google.auth.exceptions.RefreshError:
                                os.remove('token.json')
                                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                                creds = flow.run_local_server(port=0)
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
        global conn, cursor
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
        global conn, cursor
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
        global conn, cursor
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
        global conn, cursor
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
        load_dotenv("keys.env")  # This loads variables from .env into os.environ
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

def convert(messages):
        pattern = r"(\d+(?:\.\d+)?)\s*([a-z]{3})\s*(?:to|in|into)\s*([a-z]{3})"

        match = re.search(pattern, messages)
        amount = 0
        from_currency = ""
        to_currency = ""
        if match:
                amount = float(match.group(1))
                from_currency = match.group(2).upper()
                to_currency = match.group(3).upper()
        load_dotenv("keys.env")  # This loads variables from .env into os.environ
        CONVERT_ACCESS_KEY = os.getenv("CONVERT_ACCESS_KEY")
        url = f'https://api.exchangerate.host/convert?access_key={CONVERT_ACCESS_KEY}&from={from_currency}&to={to_currency}&amount={amount}'
        response = requests.get(url)
        data = response.json()
        if data.get("result") is not None:
                final_amount = data["result"]
                print('{} {} = {} {}'.format(amount, from_currency, final_amount, to_currency))
        else:
                print("❌ Conversion failed.")

class NonBlockingTimer:
    def __init__(self, duration, callback):
        self.duration = duration              # Original duration in seconds
        self.remaining = duration             # Time left
        self.callback = callback              # Function to call when done
        self._running = False
        self._thread = None

    def _run(self):
        start_time = time.time()
        self._running = True

        while self._running and self.remaining > 0:
            time.sleep(1)  # update every 1s
            elapsed = time.time() - start_time
            self.remaining = max(self.duration - elapsed, 0)

        if self._running:  # Timer finished normally
            self.callback()

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False

    def get_remaining_time(self):
        return round(self.remaining, 1)

    def get_original_time(self):
        return self.duration

def timer_done():
    print("\n⏰ Timer finished!")
    winsound.MessageBeep()

timers = None
def setuptimer(message):
        pattern = r"timer\s+for\s+(\d+)\s*(sec|second|seconds|min|minute|minutes)?"
        match = re.search(pattern, message, re.IGNORECASE)
        seconds = 0
        global timers
        if match:
                value = int(match.group(1))
                unit = match.group(2) or "seconds"
                if unit.lower().startswith("min"):
                        value *= 60
                if unit.lower().startswith("hour"):
                        value *= 3600
                seconds = value
                timers = NonBlockingTimer(seconds, timer_done)
                timers.start()
                print("Timer set for " + str(seconds) + " seconds.")
                return

        if re.search(r"(how much time|time left|remaining time)", message, re.IGNORECASE):
                if timers:
                        if timers.get_remaining_time() == 0:
                                print("\n⏰ Timer finished!")
                                return
                        total_seconds = timers.get_remaining_time()
                        hours = total_seconds // 3600
                        remainder = total_seconds % 3600
                        minutes = remainder // 60
                        seconds = remainder % 60
                        if hours == 0:
                                if minutes == 0:
                                        print(str(seconds) + " seconds remaining on the timer")
                                else:
                                        print(str(minutes) + " mins and " + str(seconds) + " seconds remaining on the timer")
                        else:
                                print(str(hours) + " hours and " + str(minutes) + " mins and " + str(seconds) + " seconds remaining on the timer")
                else:
                        print("No timers found.")

def websearch(message):
        lst = []
        query = message.lower().replace("search for ", "")
        with DDGS() as ddgs:
                results = ddgs.text(query, max_results=20)
                #for i, result in enumerate(results, start=1):
                #        print(f"{i}. {result['title']} - {result['href']}")
                lst.extend(results)
                #result elements: title, href, body
        return lst
model = None
def get_domain_boost(url):
    if ".gov" in url or ".edu" in url:
        return 3
    elif any(domain in url for domain in ["nytimes.com", "bbc.com", "forbes.com"]):
        return 2
    elif ".org" in url:
        return 1
    return 0

def rank_results(search_results):
    ranked_results = []
    for url, title, similarity_score in search_results:
        professionalism = get_domain_boost(url)
        total_score = similarity_score + professionalism  # combine relevance + professionalism
        ranked_results.append((url, title, total_score))

    ranked_results.sort(key=lambda x: x[2], reverse=True)
    return ranked_results

def pick_top_k(links, titles, message, k=3, similarity_threshold=0.75):
        # Embed titles and statement
        title_embeddings = model.encode(titles, convert_to_tensor=True)
        statement_embedding = model.encode(message, convert_to_tensor=True)

        # Compute similarity scores to statement
        sims = util.cos_sim(statement_embedding, title_embeddings)[0]
        # Sort titles by relevance (descending)
        sorted_indices = sims.argsort(descending=True)

        selected = []
        selected_indices = []
        """
        for idx in sorted_indices:
                if len(selected) == k:
                        break
                candidate_embedding = title_embeddings[idx]

                # Check similarity with already selected titles
                is_redundant = False
                for sel_idx in selected_indices:
                        sim_score = util.cos_sim(candidate_embedding, title_embeddings[sel_idx])[0].item()
                        if sim_score > similarity_threshold:
                                is_redundant = True
                                break

                if not is_redundant:
                        selected.append(titles[idx])
                        selected_indices.append(idx)
        """
        i = 0
        search_results = []
        similarity_lst = sims.tolist()
        for j in links:
                search_results.append((j['href'], j['title'], similarity_lst[i]))
                i = i + 1
        ranked = rank_results(search_results)
        final_lst = []
        final_lst.append(ranked[0][1])
        final_lst.append(ranked[1][1])
        final_lst.append(ranked[2][1])
        return(final_lst)  # Top 3 results

def rankUrl(lst, message):
        titles = []
        links = []
        body = []
        for result in lst:
                titles.append(result['title'])
                links.append(result['href'])
                body.append(result['body'])

        return pick_top_k(lst, titles, message, k=3)

def filter_english_titles(titles):
    english_titles = []
    for title in titles:
        try:
            if detect(title) == 'en':  # Keep only English
                english_titles.append(title)
        except:
            continue  # Skip titles that cannot be detected
    return english_titles

def extract_clean_text(url):
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        return trafilatura.extract(downloaded)
    return None

summarizer = None
def safe_summarize(text, default_max_length=800, default_min_length=150, chunk_size=800):
    if not text or not text.strip():
        return "No content to summarize."

    words = text.split()
    summaries = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]).strip()

        if not chunk:
            continue

        chunk_word_count = len(chunk.split())

        # If the chunk is too small, just keep it as-is
        if chunk_word_count < 50:
            summaries.append(chunk)
            continue

        try:
            dynamic_max_length = min(default_max_length, max(50, chunk_word_count // 2))
            dynamic_min_length = min(default_min_length, max(10, chunk_word_count // 6))

            result = summarizer(
                chunk,
                max_length=dynamic_max_length,
                min_length=dynamic_min_length,
                do_sample=False
            )

            if result and isinstance(result, list) and "summary_text" in result[0]:
                summaries.append(result[0]["summary_text"])
            else:
                summaries.append(chunk)  # fallback if summarizer fails
        except Exception:
            # ✅ No more repeated errors: just use the chunk itself
            summaries.append(chunk)

    if not summaries:
        return "No valid chunks to summarize."

    merged_summary = " ".join(summaries)

    # Summarize the merged result only if we actually summarized multiple chunks
    if len(summaries) > 1:
        try:
            merged_word_count = len(merged_summary.split())
            dynamic_max_length = min(default_max_length, max(50, merged_word_count // 2))
            dynamic_min_length = min(default_min_length, max(10, merged_word_count // 6))

            result = summarizer(
                merged_summary,
                max_length=default_max_length,
                min_length=default_min_length,
                do_sample=False
            )
            return result[0]["summary_text"]
        except Exception:
            return merged_summary

    return summaries[0]

def search_AI(message):
        """
        Step 1:  web.search("latest iPhone model 2025") and get 10-20 links
        E.x. Bing results:
           1. "Apple launches iPhone 17 Pro Max" – technews.com
           2. "Everything about iPhone 17" – apple.com
           ....
           20. "What is the iPhone 17" - news.com
        ↓
        Step 2: rank the sources using: Query match, Source credibility, Freshness, Diversity and Redundancy removal.
        Model reads snippets, picks best sources and pick the top 1–3 results after scoring
        ↓
        Step 3: Extract the info of the top 1-3 links
        ↓
        Step 4: Extract the relevant paragraphs and summarizes + merges the data to generates response:
"""
        urls = websearch(message)
        if not urls:
                print("Failed because can't search for topic")
                return
        ranked_urls = rankUrl(urls, message)
        if not ranked_urls:
                print("Failed because no titles were similar")
                return
        ranked_english_titles = filter_english_titles(ranked_urls)
        if not ranked_english_titles:
                print("Failed because no english titles found")
                return
        main_text = []
        for i in urls:
                for j in ranked_english_titles:
                        if i['title'] == j:
                                main_text.append(extract_clean_text(i['href']))
        if not main_text:
                print("Failed because no matches found")
                return
        for i in main_text[:]:
                if i == None:
                        main_text.remove(i)
        merged_text = "\n\n".join(main_text)

        try:
                summary = safe_summarize(merged_text)
                print(summary)
        except (ValueError, IndexError):
                print("Failed to Summarize")
                if len(main_text[0]) > 500:
                        print(main_text[0][:500])
                else:
                        print(main_text[0])

def show_image(filename):
        img = Image.open(filename)
        img.show()

def generate_image(prompt):
    load_dotenv("keys.env")
    GENERATE_API_TOKEN = os.getenv("GENERATE_API_KEY")
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {
        "Authorization": f"Bearer {GENERATE_API_TOKEN}"
    }
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    text = prompt
    first_three = " ".join(text.split()[:3])
    filename = "images\\" + first_three + ".png"
    counter = 1
    while os.path.exists(filename):
            filename = "images\\" + first_three + "{" + str(counter) + "}.png"
            counter += 1
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Image saved at {filename}")
        show_image(filename)
    else:
        print("Error:", response.status_code, response.text)

def download_video(prompt):
        pipe = DiffusionPipeline.from_pretrained("damo-vilab/text-to-video-ms-1.7b", torch_dtype=torch.float32)
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        filename = "videos\\" + first_three + ".png"
        counter = 1
        while os.path.exists(filename):
                filename = "videos\\" + first_three + "{" + str(counter) + "}.png"
                counter += 1
        video_frames = pipe(prompt, num_frames=48, num_inference_steps=25).frames
        video_path = export_to_video(video_frames[0], output_video_path=videos)
        print(f"Text To Video Complete: Video saved at {video_path}")

def generate_video(prompt):
        threading.Thread(target=download_video, daemon=True, args=(prompt)).start()


def secondaryfunction():
        ppid = os.getppid()
        try:
                while(1):
                        user = input("Waiting for AI Input: ")
                        with open("command_history.txt", "a") as f:
                                f.write("Command: " + user + ".\n")
                        lower_user = user.lower()
                        if lower_user.startswith("schedule"):
                                schedule(user)
                        elif lower_user.startswith("cancel"):
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
                        elif lower_user.startswith("convert"):
                                convert(lower_user)
                        elif "time" in lower_user:
                                setuptimer(lower_user)
                        elif user.startswith("hello AI"):
                                response = AI(user[len("hello AI"):].lstrip())
                                print("AI response: " + response)
                        elif user == "close AI":
                                os._exit(1)
                        elif user.startswith("translate"):
                                translate_t(user)
                        elif lower_user.startswith("search for"):
                                search_AI(user)
                        elif lower_user.startswith("generate image"):
                            match = re.match(r"generate image (.+)", lower_user)
                            if match:
                                prompt = match.group(1) if match else ""
                                generate_image(prompt)
                        elif lower_user.startswith("generate video"):
                                match = re.match(r"generate video (.+)", lower_user)
                                if match:
                                        prompt = match.group(1) if match else ""
                                        generate_video(prompt)
                        else:
                                response = AI(user)
                                if "cannot" in response[:200] and "real-time" in response[:200]:
                                        search_AI(user)
                                else:
                                        print("AI response: " + response)
        except BaseException as e:
                result = subprocess.run(["tasklist", "/FI", f"PID eq {ppid}"], capture_output=True, text=True)
                if "python" in result.stdout:
                        if os.getpid() != ppid:
                                print("Secondary received Ctrl+C. Killing mainprocess...")
                                proc = psutil.Process(ppid)
                                proc.terminate()
                                print("Mainprocess terminated.")
                print("An error occured: ", repr(e))
                sys.exit(0)

if __name__ == "__main__":
        #global fastmodel, summarizer, new_creds, model
        fastmodel = fasttext.load_model('lid.176.ftz')
        new_creds = loadCred()
        setup_db()
        model = SentenceTransformer('all-MiniLM-L6-v2')
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        with open("command_history.txt", "w") as f:
                f.write("Models Loaded.\n")
        print("Models Loaded.")
        secondaryfunction()

