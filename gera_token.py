from jose import jwt
import os
alg = os.getenv("AUTH_ALG", "HS512")
secret = os.getenv("JWT_SECRET", "supersegredo")
claims = {"sub":"user-123", "iss": os.getenv("JWT_ISSUER","Insper::PMA")}
print(jwt.encode(claims, secret, algorithm=alg))
