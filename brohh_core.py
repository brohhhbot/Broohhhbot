import subprocess, requests, time, threading
from config import GEMINI_KEY, TG_TOKEN, TG_CHAT, MODEL

def tg_sync(x):
    try: requests.post("https://api.telegram.org/bot"+TG_TOKEN+"/sendMessage",data={"chat_id":TG_CHAT,"text":x})
    except: pass
def tg(x):
    threading.Thread(target=tg_sync,args=(x,),daemon=True).start()
def listen():
    return subprocess.run(["termux-speech-to-text"],capture_output=True,text=True).stdout.strip().lower()
def speak(x):
    subprocess.run(["termux-tts-speak","-l","hi","-r","1.15",x])
def ask(q):
    u="https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+":generateContent?key="+GEMINI_KEY
    b={"contents":[{"parts":[{"text":"Hamesha shuddh Hindi (Devanagari) mein sirf 1-2 chhote vaakya mein jawab do: "+q}]}]}
    err=""
    for _ in range(3):
        try:
            d=requests.post(u,json=b,timeout=15).json()
            if "candidates" in d: return d["candidates"][0]["content"]["parts"][0]["text"]
            err=str(d.get("error",d))[:150]
        except Exception as e:
            err=str(e)[:150]
        time.sleep(1)
    tg("Gemini error: "+err)
    return "Gemini se jawab nahi mila"
def handle(c):
    if "youtube" in c or "यूट्यूब" in c:
        subprocess.run(["am","start","-a","android.intent.action.VIEW","-d","https://youtube.com"]); speak("यूट्यूब खोल दिया")
    else:
        a=ask(c); tg("Jawab: "+a); speak(a)

tg("Brohh start hua")
while True:
    try:
        subprocess.run(["termux-dialog","confirm","-t","Brohh","-i","Bolna hai?"],capture_output=True)
        speak("बोलो")
        c=listen()
        tg("Suna: "+c)
        if c: handle(c)
    except Exception as e:
        tg("Brohh error: "+str(e)); time.sleep(5)
  
