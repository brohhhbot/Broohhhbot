import subprocess, requests, time, threading, base64, os, json, re, difflib
from config import GEMINI_KEY, TG_TOKEN, TG_CHAT, MODEL
try:
    from config import CITY
except Exception:
    CITY=""
REC=os.path.expanduser("~/rec.m4a")
CONTACTS={}

def sh(*a):
    return subprocess.run(list(a),capture_output=True,text=True).stdout
def tg_sync(x):
    try: requests.post("https://api.telegram.org/bot"+TG_TOKEN+"/sendMessage",data={"chat_id":TG_CHAT,"text":x})
    except: pass
def tg(x):
    threading.Thread(target=tg_sync,args=(x,),daemon=True).start()
def speak(x):
    subprocess.run(["termux-tts-speak","-l","hi","-r","1.15",x])
def confirm(msg):
    return '"yes"' in sh("termux-dialog","confirm","-t","Brohh","-i",msg)

def load_contacts():
    try:
        for c in json.loads(sh("termux-contact-list")):
            n=c.get("name"); p=c.get("number")
            if n and p: CONTACTS[n]=re.sub(r"[^\d+]","",p)
    except Exception: pass
def find(x):
    d=re.sub(r"[ -]","",x)
    if re.fullmatch(r"\+?\d{6,15}",d): return x,d
    m=difflib.get_close_matches(x,list(CONTACTS),n=1,cutoff=0.5)
    return (m[0],CONTACTS[m[0]]) if m else (None,None)

def record():
    if os.path.exists(REC): os.remove(REC)
    subprocess.run(["termux-microphone-record","-f",REC,"-l","0"],capture_output=True)
    subprocess.run(["termux-vibrate","-d","150"])
    subprocess.run(["termux-dialog","confirm","-t","Brohh","-i","सुन रहा हूँ... बोलना खत्म होने पर OK दबाओ"],capture_output=True)
    subprocess.run(["termux-microphone-record","-q"],capture_output=True)
    time.sleep(1)
    return open(REC,"rb").read() if os.path.exists(REC) else b""

def prompt():
    return ("Tum Brohh ho, ek Hindi voice assistant. Audio sunke jawab do, hamesha shuddh Hindi (Devanagari) mein, sirf 1-2 chhote vaakya. "
    "Abhi ka samay: "+time.strftime("%H:%M")+". "
    "Mausam ya news poochhe to Google Search se taaza jaankari lo. Mausam ka default shahar: "+(CITY or "jo user bole")+". "
    "Agar user koi kaam karwana chahe to sirf ek line likho, kuch aur nahi: "
    "CMD|YOUTUBE ya CMD|CALL|contact ka naam ya number ya CMD|SMS|contact ka naam ya number|message "
    "ya CMD|TORCH|on ya off ya CMD|VOLUME|up ya down ya 0 se 15 ka number "
    "ya CMD|ALARM|HH|MM|label (24 ghante) ya CMD|TIMER|seconds|label. "
    "Contact ka naam in mein se exact chuno: "+", ".join(list(CONTACTS)[:150]))

def call_gemini(data,tools):
    u="https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+":generateContent?key="+GEMINI_KEY
    b={"contents":[{"parts":[{"text":prompt()},{"inline_data":{"mime_type":"audio/aac","data":base64.b64encode(data).decode()}}]}]}
    if tools: b["tools"]=[{"google_search":{}}]
    return requests.post(u,json=b,timeout=40).json()
def ask_audio(data):
    err=""
    for i in range(3):
        try:
            d=call_gemini(data,i<2)
            if "candidates" in d:
                t="".join(p.get("text","") for p in d["candidates"][0].get("content",{}).get("parts",[])).strip()
                if t: return t
            err=str(d.get("error",d))[:150]
        except Exception as e:
            err=str(e)[:150]
        time.sleep(1)
    tg("Gemini error: "+err)
    return "Gemini se jawab nahi mila"

def ring(label):
    for _ in range(3):
        subprocess.run(["termux-vibrate","-d","800"]); speak("टाइमर पूरा हुआ "+label)

def handle(a):
    m=re.search(r"CMD\|(.*)",a)
    if not m:
        tg("Jawab: "+a); speak(a); return
    p=[x.strip() for x in m.group(1).split("|")]
    act=p[0].upper()
    tg("Kaam: "+m.group(1))
    if act=="YOUTUBE":
        sh("am","start","-a","android.intent.action.VIEW","-d","https://youtube.com"); speak("यूट्यूब खोल दिया")
    elif act=="CALL" and len(p)>1:
        n,num=find(p[1])
        if not num: speak("ये नंबर नहीं मिला"); return
        if confirm(n+" को कॉल करूँ?"): sh("termux-telephony-call",num); speak("कॉल लगा रहा हूँ")
    elif act=="SMS" and len(p)>2:
        n,num=find(p[1]); msg="|".join(p[2:])
        if not num: speak("ये नंबर नहीं मिला"); return
        if confirm(n+" को भेजूँ: "+msg): sh("termux-sms-send","-n",num,msg); speak("मैसेज भेज दिया")
    elif act=="TORCH" and len(p)>1:
        sh("termux-torch","on" if p[1].lower()=="on" else "off"); speak("टॉर्च "+("चालू" if p[1].lower()=="on" else "बंद"))
    elif act=="VOLUME" and len(p)>1:
        try:
            mx=15; cur=0
            for s in json.loads(sh("termux-volume")):
                if s["stream"]=="music": mx=s["max_volume"]; cur=s["volume"]
            v=min(mx,cur+3) if p[1]=="up" else max(0,cur-3) if p[1]=="down" else min(mx,max(0,int(p[1])))
            sh("termux-volume","music",str(v)); speak("आवाज़ बदल दी")
        except Exception as e:
            tg("Volume error: "+str(e))
    elif act=="ALARM" and len(p)>2:
        sh("am","start","-a","android.intent.action.SET_ALARM","--ei","android.intent.extra.alarm.HOUR",str(int(p[1])),"--ei","android.intent.extra.alarm.MINUTES",str(int(p[2])),"--es","android.intent.extra.alarm.MESSAGE",(p[3] if len(p)>3 else "Brohh"),"--ez","android.intent.extra.alarm.SKIP_UI","true")
        speak("अलार्म लगा दिया")
    elif act=="TIMER" and len(p)>1:
        threading.Timer(int(p[1]),ring,args=((p[2] if len(p)>2 else ""),)).start(); speak("टाइमर लगा दिया")
    else:
        speak("ये काम समझ नहीं आया")

load_contacts()
tg("Brohh start hua")
while True:
    try:
        subprocess.run(["termux-dialog","confirm","-t","Brohh","-i","Bolna hai?"],capture_output=True)
        data=record()
        if len(data)>1000: handle(ask_audio(data))
        else: tg("Recording khali aayi")
    except Exception as e:
        tg("Brohh error: "+str(e)); time.sleep(5)
