"""Sends one push notification through Firebase Cloud Messaging (FCM HTTP v1 API).

Signs in with the Firebase Admin SDK service-account key (FIREBASE_CREDENTIALS_FILE); google-auth
fetches and refreshes the access token.
"""

import logging
from functools import lru_cache
from typing import Literal

import requests
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

from app.core.config import settings

logger = logging.getLogger(__name__)

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
CHANNEL_ID = "reminders"  # the Android notification channel the mobile app creates
TIMEOUT_SECONDS = 10

# sent: delivered to FCM · dead: token no longer valid, delete it · failed: FCM or network trouble, try later
SendResult = Literal["sent", "dead", "failed"]


@lru_cache
def _fcm() -> tuple[AuthorizedSession, str]:
    """(session that adds the access token, FCM send URL). Raises if the key file is missing or invalid."""
    if not settings.FIREBASE_CREDENTIALS_FILE:
        raise RuntimeError("FIREBASE_CREDENTIALS_FILE is not set")
    credentials = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
        settings.FIREBASE_CREDENTIALS_FILE, scopes=[FCM_SCOPE]
    )
    url = f"https://fcm.googleapis.com/v1/projects/{credentials.project_id}/messages:send"
    logger.info("FCM ready: project=%s", credentials.project_id)
    return AuthorizedSession(credentials), url  # type: ignore[no-untyped-call]


def check_credentials() -> None:
    """Fails at worker start, with a clear message, instead of on the first due reminder."""
    _fcm()


def send(token: str, title: str, body: str, data: dict[str, str]) -> SendResult:
    session, url = _fcm()
    message = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": body},
            "data": data,  # values must be strings
            "android": {"priority": "high", "notification": {"channel_id": CHANNEL_ID}},
        }
    }
    try:
        res = session.post(url, json=message, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.warning("FCM unreachable: %s", exc)
        return "failed"

    if res.ok:
        return "sent"
    if _is_dead_token(res):
        logger.info("FCM token no longer valid (HTTP %s): %s…", res.status_code, token[:12])
        return "dead"
    logger.warning("FCM send failed: HTTP %s %s", res.status_code, res.text[:300])
    return "failed"


def _is_dead_token(res: requests.Response) -> bool:
    """UNREGISTERED: app uninstalled or token expired. SENDER_ID_MISMATCH: token from another Firebase
    project. A 400 about the registration token: not a valid token."""
    if res.status_code == 404:
        return True
    text = res.text
    return (
        "UNREGISTERED" in text
        or "SENDER_ID_MISMATCH" in text
        or (res.status_code == 400 and "registration token" in text)
    )
