import os, secrets, mimetypes
from functools import wraps
from io import BytesIO
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import requests

app=Flask(__name__)
app.secret_key=os.getenv("FLASK_SECRET_KEY","replace-this-secret-before-deploy")
app.config.update(MAX_CONTENT_LENGTH=25*1024*1024, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE","true").lower()=="true")
LUMINA=os.getenv("LUMINA_API_KEY","").strip()
VOICE=os.getenv("REPLICAVOX_API_KEY","").strip()
PASSWORD=os.getenv("APP_PASSWORD","").strip()
LUMINA_URL="https://api.zukoxmd.my.id/api/v1/ai/chat"
RV="https://api.replicavox.com/v1"
AUDIO_EXT={".wav",".mp3",".m4a",".ogg",".flac",".webm"}

def auth(f):
    @wraps(f)
    def wrapped(*a,**kw):
        if not session.get("ok"): return jsonify({"error":"Please sign in again."}),401
        return f(*a,**kw)
    return wrapped

@app.after_request
def headers(r):
    r.headers["X-Content-Type-Options"]="nosniff"
    r.headers["X-Frame-Options"]="DENY"
    r.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    return r

@app.get("/")
def home():
    return render_template("index.html") if session.get("ok") else render_template("login.html")

@app.post("/login")
def login():
    if PASSWORD and secrets.compare_digest(request.form.get("password",""),PASSWORD):
        session.clear(); session["ok"]=True
        return redirect(url_for("home"))
    return render_template("login.html",error="Incorrect password or APP_PASSWORD is not configured."),401

@app.post("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.get("/health")
def health(): return jsonify({"ok":True,"service":"Voices Clone AI"})

@app.get("/api/status")
@auth
def status(): return jsonify({"lumina":bool(LUMINA),"voice":bool(VOICE)})

@app.post("/api/chat")
@auth
def chat():
    if not LUMINA: return jsonify({"error":"Lumina key is not configured on the server."}),503
    q=(request.json or {}).get("q","").strip()
    if not q or len(q)>6000: return jsonify({"error":"Enter a message up to 6,000 characters."}),400
    try:
        r=requests.get(LUMINA_URL,params={"q":q},headers={"Authorization":f"Bearer {LUMINA}"},timeout=90)
        try: d=r.json()
        except Exception: d={"response":r.text[:12000]}
        return (jsonify(d),r.status_code)
    except requests.RequestException: return jsonify({"error":"Lumina connection failed."}),502

@app.get("/api/clones")
@auth
def clones():
    if not VOICE: return jsonify({"error":"Replicavox key is not configured."}),503
    try:
        r=requests.get(RV+"/audio/clones",headers={"Authorization":f"Bearer {VOICE}"},timeout=30)
        return (r.content,r.status_code,{"Content-Type":r.headers.get("Content-Type","application/json")})
    except requests.RequestException: return jsonify({"error":"Voice provider connection failed."}),502

@app.post("/api/clones")
@auth
def create_clone():
    if not VOICE: return jsonify({"error":"Replicavox key is not configured."}),503
    if request.form.get("consent")!="yes": return jsonify({"error":"Confirm you own this voice or have the speaker's explicit permission."}),400
    name=request.form.get("name","").strip(); lang=request.form.get("language","en")
    f=request.files.get("file")
    if not name or not f: return jsonify({"error":"Voice name and audio sample are required."}),400
    ext=os.path.splitext(f.filename or "")[1].lower()
    if ext not in AUDIO_EXT: return jsonify({"error":"Use WAV, MP3, M4A, OGG, FLAC or WebM."}),400
    raw=f.read()
    if not raw or len(raw)>25*1024*1024: return jsonify({"error":"Audio must be valid and no larger than 25 MB."}),400
    try:
        files={"file":(secrets.token_hex(8)+ext,BytesIO(raw),mimetypes.guess_type("x"+ext)[0] or "application/octet-stream")}
        r=requests.post(RV+"/audio/clones",headers={"Authorization":f"Bearer {VOICE}"},data={"name":name,"language":lang},files=files,timeout=120)
        try: d=r.json()
        except Exception: d={"error":r.text[:2000]}
        return jsonify(d),r.status_code
    except requests.RequestException: return jsonify({"error":"Clone request failed. Please retry."}),502

@app.post("/api/tts")
@auth
def tts():
    if not VOICE: return jsonify({"error":"Replicavox key is not configured."}),503
    d=request.json or {}; text=d.get("text","").strip(); voice=d.get("voice","Archer")
    lang=d.get("language","en"); speed=float(d.get("speed",1)); fmt=d.get("format","mp3")
    if not text or len(text)>10000: return jsonify({"error":"Enter text up to 10,000 characters."}),400
    if fmt not in {"mp3","wav","opus","flac","aac","pcm"} or not .25<=speed<=4: return jsonify({"error":"Invalid format or speed."}),400
    try:
        r=requests.post(RV+"/audio/speech",headers={"Authorization":f"Bearer {VOICE}","Content-Type":"application/json"},
            json={"model":"replicavox-expressive-v2","voice":voice,"input":text,"language":lang,"speed":speed,"response_format":fmt},timeout=180)
        if not r.ok:
            try: e=r.json()
            except Exception: e={"error":f"Voice provider returned HTTP {r.status_code}"}
            return jsonify(e),r.status_code
        return send_file(BytesIO(r.content),mimetype=r.headers.get("Content-Type","audio/mpeg"),
                         as_attachment=True,download_name="voices-clone-output."+fmt)
    except requests.RequestException: return jsonify({"error":"Speech generation timed out or provider is unavailable."}),502

@app.errorhandler(413)
def too_big(_): return jsonify({"error":"Upload exceeds 25 MB."}),413

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT","8000")))
