from __future__ import print_function
import os
import psutil
import subprocess
import sys
import asyncio
from googletrans import Translator
import builtins
import functools
from langdetect import detect
import fasttext
import langid
import dateparser
import win32com.client
import spacy
import re
from datetime import datetime, timedelta
from tzlocal import get_localzone_name
from dateparser.search import search_dates
from sympy.physics.mechanics import body

import datetime
import os.path
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
        print(src_lang + " " + dest_lang)
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
                print("I don't know your language, defualt translate to english")
                dest_lang = 'en'
        #src_lang = detect(user)
        #numpy library must be 1.26.4
        labels, probs = fastmodel.predict(user)
        src_lang = labels[0].replace('__label__', '')
        result_text = asyncio.run(translate_text(user, src_lang, dest_lang))
        print(result_text)

def test():
        user = """Summarize this email: Subject: Application for [Job Title] - [Your Name]

Dear [Hiring Manager Name],

I am writing to express my strong interest in the [Job Title] position at [Company Name], as advertised on [Platform where you saw the ad - e.g., company website, LinkedIn, etc.]. I was particularly drawn to [mention something specific about the company or role that excites you] and believe my skills and experience align well with the requirements of this role.

With [Number] years of experience in [Your Field], I have a proven track record of success in [mention 1-2 key accomplishments relevant to the job]. For example, in my previous role at [Previous Company], I [briefly describe a relevant accomplishment and its positive outcome]. I am proficient in [list 2-3 relevant skills, e.g., project management, data analysis, communication]. {Link: According to Jobstreet.com https://ph.jobstreet.com/career-advice/article/great-job-application-email}, I am also a highly motivated and results-oriented individual.

I am confident that I can make a significant contribution to [Company Name] and am eager to learn more about this opportunity. My resume, which is attached, provides further details on my qualifications and experience.

Thank you for your time and consideration. I look forward to hearing from you soon.

Sincerely,"""
        response = AI(user)
        print("AI response: " + response)

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

def secondaryfunction():
        ppid = os.getppid()
        try:
                while(1):
                        user = input("Waiting for AI Input: ")
                        if user == "Excel":
                                excel()
                        elif user == "internet":
                                internet()
                        elif user == "music":
                                media()
                        elif user == "test":
                                test()
                        elif user.startswith("Schedule"):
                                schedule(user)
                        elif user.startswith("Cancel"):
                                Cancelschedule(user)
                        elif user.startswith("hello AI"):
                                response = AI(user[len("hello AI"):].lstrip())
                                print("AI response: " + response)
                        elif user == "close AI":
                                os._exit(1)
                        elif user.startswith("translate"):
                                translate_t(user)
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
        print("Start of Secondary")
        fastmodel = fasttext.load_model('lid.176.ftz')
        new_creds = loadCred()
        secondaryfunction()

