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
from langdetect import detect
import langid
import fasttext
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
