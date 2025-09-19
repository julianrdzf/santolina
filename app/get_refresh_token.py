import os
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 🔹 Scopes que necesitamos
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# 🔹 Tus credenciales de Google Cloud
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=SCOPES,
)

# 🔹 Access type "offline" para obtener refresh token
# Si estás en un entorno con navegador:
creds = flow.run_local_server(port=0)

# 🔹 Si estás en un servidor sin GUI, usar:
# creds = flow.run_local_server(port=0, open_browser=False)

print("Access Token:", creds.token)
print("Refresh Token:", creds.refresh_token)
print("Client ID:", GMAIL_CLIENT_ID)
print("Client Secret:", GMAIL_CLIENT_SECRET)