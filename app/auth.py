from fastapi import HTTPException, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.settings import settings

# define o esquema de segurança p/ o OpenAPI
bearer = HTTPBearer(auto_error=False)

async def require_auth(
    authorization: HTTPAuthorizationCredentials | None = Security(bearer),
    id_account_header: str | None = Header(default=None, alias="id-account"),
) -> dict:
    # 1) se o gateway mandou id-account no header, use-o
    if id_account_header:
        return {"id-account": str(id_account_header)}

    # 2) caso contrário, tente decodificar o Bearer
    if not authorization:
        raise HTTPException(status_code=401, detail="missing bearer token")

    token = authorization.credentials
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS512"],
            options={"verify_aud": False},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token")

    account_id = claims.get("id-account") or claims.get("id") or claims.get("sub")
    if not account_id:
        raise HTTPException(status_code=400, detail="missing account id")

    return {"id-account": str(account_id)}
