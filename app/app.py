from fastapi import FastAPI, Depends, HTTPException
from app.clientes.providers import fetch_rate
from app.models import QuoteOut
from app.auth import require_auth
from app.settings import settings

app = FastAPI(title="Exchange API", version="1.0.0")

@app.get("/exchange/{from_curr}/{to_curr}", response_model=QuoteOut)
async def get_exchange(from_curr: str, to_curr: str, claims: dict = Depends(require_auth)):
    try:
        rate, date = await fetch_rate(from_curr, to_curr)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"rate provider error: {e!s}")

    half = settings.spread / 2.0
    sell = round(rate * (1 + half), 6)
    buy  = round(rate * (1 - half), 6)

    account_id = claims["id-account"]
    return {"sell": sell, "buy": buy, "date": date, "id-account": str(account_id)}
