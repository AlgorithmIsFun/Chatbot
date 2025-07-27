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
        secondaryfunction()

