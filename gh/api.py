"""Minimaler Client für die Geizhals Partner-API (v9).

Authentifizierung laut Doku: pro Request ein HS256-JWT, signiert mit dem
Shared Secret des Accounts. Payload:
  { token_id: <user>, timestamp: <epoch>, request_fingerprint: sha256(
      METHOD|HOST|QUERY_STRING|BODY) }
"""
import hashlib
import json
import time

import jwt
import requests

HOST = "api.geizhals.net"
BASE = "/gh/v9"


class GeizhalsError(RuntimeError):
    pass


class GeizhalsAPI:
    def __init__(self, user, secret, loc="de", lang="de", timeout=60):
        if not user or not secret:
            raise GeizhalsError("GEIZHALS_USER und GEIZHALS_SECRET müssen gesetzt sein")
        self.user = user
        self.secret = secret
        self.loc = loc
        self.lang = lang
        self.timeout = timeout
        self.session = requests.Session()
        self.calls = 0

    def _token(self, body):
        fingerprint = "|".join(["POST", HOST, "", body])
        payload = {
            "token_id": self.user,
            "timestamp": int(time.time()),
            "request_fingerprint": hashlib.sha256(fingerprint.encode("utf-8")).hexdigest(),
        }
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        return token.decode("ascii") if isinstance(token, bytes) else token

    def post(self, endpoint, payload, retries=5):
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        url = f"https://{HOST}{BASE}/{endpoint.lstrip('/')}"
        for attempt in range(retries):
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + self._token(body),
            }
            resp = self.session.post(url, data=body.encode("utf-8"), headers=headers,
                                     timeout=self.timeout)
            self.calls += 1
            if resp.status_code == 200:
                return resp.json()
            retryable = resp.status_code in (429, 500, 502, 503, 504)
            try:
                retryable = retryable or bool(resp.json().get("retry"))
            except ValueError:
                pass
            if retryable and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise GeizhalsError(f"{endpoint}: HTTP {resp.status_code}: {resp.text[:300]}")
        raise GeizhalsError(f"{endpoint}: keine Antwort")

    # --- Endpunkte -------------------------------------------------------

    def categories(self, m=None):
        params = {"lang": self.lang}
        if m is not None:
            params["m"] = m
        return self.post("categories", {"params": params}).get("categories", [])

    def categorylist(self, category, **params):
        params.setdefault("loc", self.loc)
        params.setdefault("lang", self.lang)
        return self.post("categorylist", {"category": category, "params": params}).get("response", {})

    def bestprice_development(self, **params):
        params.setdefault("loc", self.loc)
        return self.post("bestprice_development", {"params": params}).get("response", {})

    def query_product(self, query, type_="id", **params):
        params.setdefault("loc", self.loc)
        return self.post("query_product", {"query": str(query), "type": type_, "params": params})
