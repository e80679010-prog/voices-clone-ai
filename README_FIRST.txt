VOICES CLONE AI — DEPLOYABLE STARTER

Features:
- Password-protected private workspace
- Replicavox voice cloning and text-to-speech
- Lumina AI chat using the exact chat endpoint supplied
- Responsive mobile + desktop interface
- Image and video panels prepared but inactive until verified endpoints are supplied

IMPORTANT: This is source code, not a live public URL. Deploy it to a hosting provider and configure environment variables.

Required hosting secrets:
APP_PASSWORD = strong unique workspace password
FLASK_SECRET_KEY = long random secret
LUMINA_API_KEY = rotated Lumina API key (the key shared in chat should be revoked)
REPLICAVOX_API_KEY = your Replicavox API key
COOKIE_SECURE = true (HTTPS hosting)

Deploy:
1. Upload this folder to a PRIVATE GitHub repository.
2. Create a Docker web service on Render, Railway or your VPS.
3. Connect the repository and select Docker deployment.
4. Add the environment variables above in the hosting dashboard.
5. Deploy and open the HTTPS URL. Sign in with APP_PASSWORD.

Local Windows test:
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Set APP_PASSWORD, FLASK_SECRET_KEY, LUMINA_API_KEY, REPLICAVOX_API_KEY and COOKIE_SECURE=false in PowerShell.
python app.py
Open http://127.0.0.1:8000

Replicavox endpoints used:
POST /v1/audio/clones (multipart file, name, language)
GET /v1/audio/clones
POST /v1/audio/speech (JSON)
Free tier documentation currently lists 15,000 characters/month, one clone, two concurrent speech requests. Free clone must be public for API use; free plan is personal-use only. Verify current provider terms.

Lumina:
Only GET https://api.zukoxmd.my.id/api/v1/ai/chat?q=... is verified from the supplied example. Image/video endpoints are not guessed.

Security:
- Keys remain server-side.
- One shared-password workspace, not multi-user SaaS.
- Audio upload is limited to 25 MB and forwarded to Replicavox without app-side permanent storage.
- Only clone your own voice or a voice with explicit permission.
- Before allowing public signups, add individual accounts, per-user quotas, abuse protection and billing.
