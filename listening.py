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
import functools
print = functools.partial(builtins.print, flush=True)
tts = None
TTS_READY = 0
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
async def translate_text(text, dest_lang='fr'):
        translator = Translator()
        result = await translator.translate(text, src='en', dest=dest_lang)
        return result.text         

def translate_t(user):
        user = user[len("translate"):].lstrip()
        lang_found = 0
        for key in my_lang:
                if user.endswith(key):
                        user = user[:-len(key)].rstrip()
                        dest_lang = my_lang[key]
                        lang_found = 1
        if lang_found == 0:
                print("I don't know your language, defualt translate to english")
                dest_lang = 'en'
        result_text = asyncio.run(translate_text(user, dest_lang))
        print(result_text)
        
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
        elif user.startswith("translate"):
                translate_t(user)

def background_task():
        #"tts_models/en/ljspeech/tacotron2-DDC" is the better model but slower
        tts = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=False)
        print("Loaded TTS Model")
        TTS_READY = 1
        
if __name__ == "__main__":
        print("Start of main")
        thread = Thread(target=background_task)
        thread.start()
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
                except KeyboardInterrupt:
                        print("Main received Ctrl+C. Killing subprocess...")
                        p.terminate()
                        p.wait()
                        print("Subprocess terminated.")
                        sys.exit(0)
