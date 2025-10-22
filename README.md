# Exchange Service (FastAPI)

## Run (local)
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
setx AUTH_ALG HS512
setx JWT_SECRET supersegredo
setx JWT_ISSUER Insper::PMA
uvicorn app:app --reload --port 8000

## Request
GET /exchange/{from}/{to}
Authorization: Bearer <JWT>

## Docker
docker build -t exchange-service:latest .
docker run -e AUTH_ALG=HS512 -e JWT_SECRET=supersegredo -p 8000:8000 exchange-service:latest
