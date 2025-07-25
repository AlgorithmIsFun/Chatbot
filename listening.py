import pyaudio,os
import speech_recognition as sr
import subprocess
import requests
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO

def excel():
        os.system("start excel.exe")

def internet():
        os.system("start chrome.exe")

def media():
        os.system("start wmplayer.exe")

def respond_voice(text):
    subprocess.run(["espeak", text])

def AI(user):
    result = subprocess.run(
        ["ollama", "run", "gemma:2b", user],
        capture_output=True,
        text=True,
	encoding="utf-8"
    )
    return result.stdout.strip()


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
    if user == "Excel":
        excel()
    elif user == "Internet":
        internet()
    elif user == "music":
        media()
    elif user.startswith("hello AI"):
        response = AI(user[len("hello AI"):].lstrip())
        print("AI response: " + response)
        respond_voice(response)

if __name__ == "__main__":
    r = sr.Recognizer()
    
    # Extend how long it waits before assuming the user is done speaking
    r.pause_threshold = 1.5        # seconds of silence before stopping recording
    r.energy_threshold = 300       # minimum audio level to detect speech
    r.dynamic_energy_threshold = True
    
    with sr.Microphone() as source:
        while 1:
            mainfunction(source)