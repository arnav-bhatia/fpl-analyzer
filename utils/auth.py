import os
import re
import uuid
import secrets
import hashlib
import base64
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = "bfcbaf69-aade-4c1b-8f00-c1cb8a193030"
URLS = {
    "auth": "https://account.premierleague.com/as/authorize",
    "start": "https://account.premierleague.com/davinci/policy/262ce4b01d19dd9d385d26bddb4297b6/start",
    "login": "https://account.premierleague.com/davinci/connections/{}/capabilities/customHTMLTemplate",
    "resume": "https://account.premierleague.com/as/resume",
    "token": "https://account.premierleague.com/as/token",
    "me": "https://fantasy.premierleague.com/api/me/",
}
STANDARD_CONNECTION_ID = "0d8c928e4970386733ce110b9dda8412"


def generate_code_verifier():
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def authenticate():
    """
    Full login flow to obtain access + refresh tokens.
    """
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    initial_state = uuid.uuid4().hex
    session = requests.Session(impersonate="chrome124")

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": "https://fantasy.premierleague.com/",
        "response_type": "code",
        "scope": "openid profile email offline_access",
        "state": initial_state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_response = session.get(URLS["auth"], params=params)
    login_html = auth_response.text

    access_token = re.search(r'"accessToken":"([^"]+)"', login_html).group(1)
    new_state = re.search(r'<input[^>]+name="state"[^>]+value="([^"]+)"', login_html).group(1)

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = session.post(URLS["start"], headers=headers).json()
    interaction_id, interaction_token = response["interactionId"], response["interactionToken"]

    email, password = os.getenv("EMAIL"), os.getenv("PASSWORD")

    response = session.post(
        URLS["login"].format(STANDARD_CONNECTION_ID),
        headers={"interactionId": interaction_id, "interactionToken": interaction_token},
        json={
            "id": response["id"],
            "eventName": "continue",
            "parameters": {"eventType": "polling"},
            "pollProps": {"status": "continue", "delayInMs": 10, "retriesAllowed": 1, "pollChallengeStatus": False},
        },
    )

    response = session.post(
        URLS["login"].format(STANDARD_CONNECTION_ID),
        headers={"interactionId": interaction_id, "interactionToken": interaction_token},
        json={
            "id": response.json()["id"],
            "nextEvent": {"constructType": "skEvent", "eventName": "continue", "params": [], "eventType": "post"},
            "parameters": {
                "buttonType": "form-submit",
                "buttonValue": "SIGNON",
                "username": email,
                "password": password,
            },
            "eventName": "continue",
        },
    ).json()

    response = session.post(
        URLS["login"].format(response["connectionId"]),
        headers=headers,
        json={
            "id": response["id"],
            "nextEvent": {"constructType": "skEvent", "eventName": "continue", "params": [], "eventType": "post"},
            "parameters": {"buttonType": "form-submit", "buttonValue": "SIGNON"},
            "eventName": "continue",
        },
    )

    response = session.post(
        URLS["resume"],
        data={"dvResponse": response.json()["dvResponse"], "state": new_state},
        allow_redirects=False,
    )
    location = response.headers["Location"]
    auth_code = re.search(r"[?&]code=([^&]+)", location).group(1)

    response = session.post(
        URLS["token"],
        data={
            "grant_type": "authorization_code",
            "redirect_uri": "https://fantasy.premierleague.com/",
            "code": auth_code,
            "code_verifier": code_verifier,
            "client_id": CLIENT_ID,
        },
    )
    tokens = response.json()
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


def refresh_tokens(refresh_token: str):
    """
    Exchange refresh token for a new access token.
    """
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(URLS["token"], data=data, headers=headers)
    return response.json()