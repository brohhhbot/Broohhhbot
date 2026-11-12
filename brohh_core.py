import subprocess, requests, time, threading, base64, os
from config import GEMINI_KEY, TG_TOKEN, TG_CHAT, MODEL
REC=os.path.expanduser("~/rec.m4a")

def tg_sync(x):
    try: requests.post("https://api.telegram.org/bot"+TG_TOKEN+"/sendMessage",data={"chat_id":TG_CHAT,"text":x})
    except: pass
def tg(x):
    threading.Thread(target=tg_sync,args=(x,),daemon=True).start()
def speak(x):
    subprocess.run(["termux-tts-speak","-l","hi","-r","1.15",x])
def record():
    if os.path.exists(REC): os.remove(REC)
    subprocess.run(["termux-microphone-record","-f",REC,"-l","0"],capture_output=True)
    subprocess.run(["termux-vibrate","-d","150"])
    subprocess.run(["termux-dialog","confirm","-t","Brohh","-i","सुन रहा हूँ... बोलना खत्म होने पर OK दबाओ"],capture_output=True)
    subprocess.run(["termux-microphone-record","-q"],capture_output=True)
    time.sleep(1)
    return open(REC,"rb").read() if os.path.exists(REC) else b""
def ask_audio(data):
    u="https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+":generateContent?key="+GEMINI_KEY
    p="Is audio mein user ne jo bola use sunke sirf 1-2 chhote vaakya mein shuddh Hindi (Devanagari) mein jawab do. Agar user YouTube kholne ko bole to sirf ek shabd YOUTUBE likho."
    b={"contents":[{"parts":[{"text":p},{"inline_data":{"mime_type":"audio/aac","data":base64.b64encode(data).decode()}}]}]}
    err=""
    for _ in range(3):
        try:
            d=requests.post(u,json=b,timeout=30).json()
            if "candidates" in d: return d["candidates"][0]["content"]["parts"][0]["text"]
            err=str(d.get("error",d))[:150]
        except Exception as e:
            err=str(e)[:150]
        time.sleep(1)
    tg("Gemini error: "+err)
    return "Gemini se jawab nahi mila"
def handle(a):
    if a.strip().upper().startswith("YOUTUBE"):
        subprocess.run(["am","start","-a","android.intent.action.VIEW","-d","https://youtube.com"]); speak("यूट्यूब खोल दिया")
    else:
        tg("Jawab: "+a); speak(a)

tg("Brohh start hua")
while True:
    try:
        subprocess.run(["termux-dialog","confirm","-t","Brohh","-i","Bolna hai?"],capture_output=True)
        data=record()
        if len(data)>1000: handle(ask_audio(data))
        else: tg("Recording khali aayi")
    except Exception as e:
        tg("Brohh error: "+str(e)); time.sleep(5)
