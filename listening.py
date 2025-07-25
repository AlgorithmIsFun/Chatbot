import pyaudio,os
import speech_recognition as sr
import subprocess
import requests
import sys
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
from TTS.api import TTS
import sounddevice as sd
from threading import Thread
tts = None
TTS_READY = 0

def excel():
        os.system("start excel.exe")

def internet():
        os.system("start chrome.exe")

def media():
        os.system("start wmplayer.exe")

def respond_voice(text):
        #subprocess.run(["espeak", text])
        wav = tts.tts(text)
        sample_rate = tts.synthesizer.output_sample_rate
        sd.play(wav, sample_rate)
        sd.wait()

def AI(user):
        result = subprocess.run(
                ["ollama", "run", "gemma:2b", user],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                encoding="utf-8"
        )
        return result.stdout.strip()

def secondaryfunction():
        while(1):
                user = input("Waiting for AI Input: ")
                print(user)
                if user == "Excel":
                        excel()
                elif user == "internet":
                        internet()
                elif user == "music":
                        media()
                elif user.startswith("hello AI"):
                        response = AI(user[len("hello AI"):].lstrip())
                        print("AI response: " + response)
                elif user == "close AI":
                        os._exit(1)
        
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
        elif user == "internet":
                internet()
        elif user == "music":
                media()
        elif user.startswith("hello AI"):
                response = AI(user[len("hello AI"):].lstrip())
                print("AI response: " + response)
                if TTS_READY == 1:
                        respond_voice(response)
        elif user == "close AI":
                os._exit(1)

def background_task():
        #"tts_models/en/ljspeech/tacotron2-DDC" is the better model but slower
        tts = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=False)
        print("Loaded TTS Model")
        TTS_READY = 1
        
if __name__ == "__main__":
        
        thread = Thread(target=background_task)
        thread.start()
        r = sr.Recognizer()
        print("Main Thread starting")
        # Extend how long it waits before assuming the user is done speaking
        r.pause_threshold = 1.5        # seconds of silence before stopping recording
        r.energy_threshold = 300       # minimum audio level to detect speech
        r.dynamic_energy_threshold = True
        Thread(target=secondaryfunction).start()
        with sr.Microphone() as source:
                while 1:
                        mainfunction(source)

