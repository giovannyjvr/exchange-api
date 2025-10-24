import datetime as dt
import httpx

async def fetch_rate(from_curr: str, to_curr: str) -> tuple[float, str]:
    """
    Busca a cotação de from_curr->to_curr em provedores públicos.
    Retorna (rate, date_iso). Lança RuntimeError se não conseguir extrair.
    """
    f = from_curr.upper()
    t = to_curr.upper()

    # 1) exchangerate.host (A)
    url_a = f"https://api.exchangerate.host/convert?from={f}&to={t}"
    # 2) frankfurter.app (B)
    url_b = f"https://api.frankfurter.app/latest?from={f}&to={t}"
    # 3) awesomeapi (C) – fallback
    url_c = f"https://economia.awesomeapi.com.br/last/{f}-{t}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # A
        try:
            r = await client.get(url_a)
            if r.status_code == 200:
                data = r.json()
                # esperado: {"success":true,"result": 5.123,"date":"2025-10-22"}
                if isinstance(data, dict) and data.get("result"):
                    rate = float(data["result"])
                    date = data.get("date") or dt.date.today().isoformat()
                    return rate, date
        except Exception:
            pass

        # B
        try:
            r = await client.get(url_b)
            if r.status_code == 200:
                data = r.json()
                # esperado: {"amount":1.0,"base":"USD","date":"2025-10-22","rates":{"BRL":5.12}}
                if isinstance(data, dict) and "rates" in data:
                    rates = data["rates"]
                    if t in rates:
                        rate = float(rates[t])
                        date = data.get("date") or dt.date.today().isoformat()
                        return rate, date
        except Exception:
            pass

        # C
        try:
            r = await client.get(url_c)
            if r.status_code == 200:
                data = r.json()
                # esperado: {"USDBRL":{"bid":"5.18", "create_date":"2025-10-04 16:30:00", ...}}
                key = f"{f}{t}"
                if isinstance(data, dict) and key in data:
                    item = data[key]
                    rate = float(item.get("bid") or 0)
                    date = (item.get("create_date") or item.get("timestamp")
                            or dt.date.today().isoformat())
                    if rate > 0:
                        return rate, date
        except Exception:
            pass

    raise RuntimeError("Provider schema not recognized or provider error")
