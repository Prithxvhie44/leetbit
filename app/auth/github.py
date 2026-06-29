from __future__ import annotations

from dataclasses import dataclass
from time import monotonic, sleep

import httpx


@dataclass(slots=True)
class GitHubDeviceFlowResult:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_in: int
    interval: int


class GitHubOAuthDeviceFlow:
    def __init__(self, client_id: str, scope: str = "repo", timeout: float = 30.0) -> None:
        self.client_id = client_id
        self.scope = scope
        self._client = httpx.Client(timeout=timeout)

    def start(self) -> GitHubDeviceFlowResult:
        response = self._client.post(
            "https://github.com/login/device/code",
            data={"client_id": self.client_id, "scope": self.scope},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub authorization response was invalid")
        return GitHubDeviceFlowResult(
            device_code=str(payload.get("device_code") or ""),
            user_code=str(payload.get("user_code") or ""),
            verification_uri=str(payload.get("verification_uri") or ""),
            verification_uri_complete=str(payload.get("verification_uri_complete") or "") or None,
            expires_in=int(payload.get("expires_in") or 0),
            interval=int(payload.get("interval") or 5),
        )

    def complete(self, device_code: str, expires_in: int, interval: int) -> str:
        deadline = monotonic() + expires_in
        current_interval = max(interval, 1)

        while True:
            if monotonic() >= deadline:
                raise RuntimeError("GitHub authorization expired before completion")

            response = self._client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("GitHub authorization response was invalid")

            access_token = str(payload.get("access_token") or "").strip()
            if access_token:
                return access_token

            error = str(payload.get("error") or "").strip()
            if error == "authorization_pending":
                sleep(current_interval)
                continue
            if error == "slow_down":
                current_interval += 5
                sleep(current_interval)
                continue
            if error == "access_denied":
                raise RuntimeError("GitHub authorization was denied by the user")
            if error == "expired_token":
                raise RuntimeError("GitHub authorization expired")
            raise RuntimeError(str(payload.get("error_description") or error or "GitHub authorization failed"))

    def close(self) -> None:
        self._client.close()