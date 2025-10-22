from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from pydantic import BaseModel
import httpx, os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from cachetools import TTLCache

AUTH_ALG = os.getenv("AUTH_ALG", "HS512").upper()
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWKS_URL = os.getenv("JWKS_URL")
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
JWT_ACCOUNT_ID_CLAIM = os.getenv("JWT_ACCOUNT_ID_CLAIM", "sub")

SPREAD_BPS = float(os.getenv("SPREAD_BPS", "50"))
EXTERNAL_API_BASE = os.getenv("EXTERNAL_API_BASE", "https://economia.awesomeapi.com.br")

app = FastAPI(title="Exchange Service", version="1.2.0")

class Quote(BaseModel):
    sell: float
    buy: float
    date: str
    id_account: str

_jwks_cache = TTLCache(maxsize=32, ttl=300)

async def _fetch_jwks() -> Dict[str, Any]:
    if not JWKS_URL:
        return {}
    if "__jwks__" in _jwks_cache:
        return _jwks_cache["__jwks__"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(JWKS_URL)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"JWKS fetch failed: {r.status_code}")
        data = r.json()
        _jwks_cache["__jwks__"] = data
        return data

async def _get_key_for_kid(kid: Optional[str]) -> Optional[Dict[str, Any]]:
    if not kid:
        return None
    if kid in _jwks_cache:
        return _jwks_cache[kid]
    jwks = await _fetch_jwks()
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            _jwks_cache[kid] = k
            return k
    return None

async def verify_and_get_account_id(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]

    try:
        if AUTH_ALG in ("HS256", "HS384", "HS512"):
            decoded = jwt.decode(
                token, JWT_SECRET, algorithms=[AUTH_ALG],
                issuer=JWT_ISSUER if JWT_ISSUER else None,
                audience=JWT_AUDIENCE.split(",") if JWT_AUDIENCE else None,
                options={"verify_aud": bool(JWT_AUDIENCE)}
            )
        elif AUTH_ALG == "RS256":
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            key = await _get_key_for_kid(kid)
            if key is None:
                jwks = await _fetch_jwks()
                keys = jwks.get("keys", [])
                if not keys:
                    raise HTTPException(status_code=401, detail="No keys in JWKS")
                key = keys[0]
            decoded = jwt.decode(
                token, key, algorithms=["RS256"],
                issuer=JWT_ISSUER if JWT_ISSUER else None,
                audience=JWT_AUDIENCE.split(",") if JWT_AUDIENCE else None,
                options={"verify_aud": bool(JWT_AUDIENCE)}
            )
        else:
            raise HTTPException(status_code=500, detail="Unsupported AUTH_ALG")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    account_id = decoded.get(JWT_ACCOUNT_ID_CLAIM) or decoded.get("account_id") or decoded.get("sub")
    if not account_id:
        raise HTTPException(status_code=401, detail="Token missing account identifier")
    return str(account_id)

async def fetch_rate(pair_from: str, pair_to: str) -> float:
    pair = f"{pair_from.upper()}-{pair_to.upper()}"
    url = f"{EXTERNAL_API_BASE}/last/{pair}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream error {r.status_code}")
        data = r.json()
        key = f"{pair_from.upper()}{pair_to.upper()}"
        if key not in data or "bid" not in data[key]:
            raise HTTPException(status_code=502, detail="Unexpected upstream response")
        return float(data[key]["bid"])

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

@app.get("/exchange/{pair_from}/{pair_to}")
async def get_exchange(pair_from: str, pair_to: str, account_id: str = Depends(verify_and_get_account_id)):
    mid = await fetch_rate(pair_from, pair_to)
    spread = SPREAD_BPS / 10_000.0
    sell = round(mid * (1 + spread), 6)
    buy = round(mid * (1 - spread), 6)
    now = datetime.now(timezone.utc).isoformat()
    return JSONResponse(content={"sell": sell, "buy": buy, "date": now, "id-account": account_id})
