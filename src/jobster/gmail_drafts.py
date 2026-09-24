from __future__ import annotations

import base64
import json
import mimetypes
import secrets
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode

import httpx


GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
GMAIL_DRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"


class GmailDraftError(RuntimeError):
    pass


@dataclass(frozen=True)
class GmailOAuthStart:
    authorization_url: str
    state: str


class GmailDraftProvider:
    """Minimal Gmail OAuth and drafts client; it intentionally exposes no send method."""

    def __init__(self, client_secret_path: str | Path, token_path: str | Path):
        self.client_secret_path = Path(client_secret_path)
        self.token_path = Path(token_path)
        self._pending_states: set[str] = set()

    def _client(self) -> dict:
        if not self.client_secret_path.exists():
            raise GmailDraftError(
                f"Gmail OAuth client file is missing: {self.client_secret_path}"
            )
        payload = json.loads(self.client_secret_path.read_text(encoding="utf-8"))
        client = payload.get("installed") or payload.get("web")
        if not isinstance(client, dict):
            raise GmailDraftError("Gmail OAuth client file has no installed or web client")
        return client

    def connected(self) -> bool:
        if not self.token_path.exists():
            return False
        try:
            token = json.loads(self.token_path.read_text(encoding="utf-8"))
            return bool(token.get("access_token") or token.get("refresh_token"))
        except (OSError, ValueError):
            return False

    def start_oauth(self, redirect_uri: str) -> GmailOAuthStart:
        client = self._client()
        state = secrets.token_urlsafe(24)
        self._pending_states.add(state)
        params = {
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GMAIL_COMPOSE_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_uri = client.get("auth_uri") or "https://accounts.google.com/o/oauth2/auth"
        return GmailOAuthStart(f"{auth_uri}?{urlencode(params)}", state)

    def finish_oauth(self, code: str, state: str, redirect_uri: str) -> None:
        if state not in self._pending_states:
            raise GmailDraftError("Gmail connection state is invalid or expired")
        self._pending_states.remove(state)
        client = self._client()
        response = httpx.post(
            client.get("token_uri") or "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client["client_id"],
                "client_secret": client["client_secret"],
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=30,
        )
        if response.is_error:
            raise GmailDraftError(f"Gmail connection failed: {response.text[:300]}")
        token = response.json()
        token["expires_at"] = time.time() + int(token.get("expires_in", 3600))
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")

    def _access_token(self) -> str:
        if not self.token_path.exists():
            raise GmailDraftError("Gmail is not connected")
        token = json.loads(self.token_path.read_text(encoding="utf-8"))
        if token.get("access_token") and float(token.get("expires_at", 0)) > time.time() + 60:
            return str(token["access_token"])
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise GmailDraftError("Gmail connection expired; reconnect Gmail")
        client = self._client()
        response = httpx.post(
            client.get("token_uri") or "https://oauth2.googleapis.com/token",
            data={
                "client_id": client["client_id"],
                "client_secret": client["client_secret"],
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        if response.is_error:
            raise GmailDraftError("Gmail connection could not be refreshed")
        refreshed = response.json()
        token.update(refreshed)
        token["refresh_token"] = refresh_token
        token["expires_at"] = time.time() + int(refreshed.get("expires_in", 3600))
        self.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")
        return str(token["access_token"])

    def create_draft(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
        attachment_path: str | Path,
    ) -> dict:
        attachment = Path(attachment_path)
        if not attachment.is_file():
            raise GmailDraftError(f"Resume file is missing: {attachment}")

        message = EmailMessage()
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        mime, _ = mimetypes.guess_type(attachment.name)
        main_type, sub_type = (mime or "application/octet-stream").split("/", 1)
        message.add_attachment(
            attachment.read_bytes(),
            maintype=main_type,
            subtype=sub_type,
            filename=attachment.name,
        )
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        response = httpx.post(
            GMAIL_DRAFTS_URL,
            headers={"Authorization": f"Bearer {self._access_token()}"},
            json={"message": {"raw": raw}},
            timeout=30,
        )
        if response.is_error:
            raise GmailDraftError(f"Gmail could not save the draft: {response.text[:300]}")
        return response.json()
