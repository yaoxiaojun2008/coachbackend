from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from jose import jwt, JWTError
import requests
import json

security = HTTPBearer()

# Cache for JWKS to avoid fetching on every request
_cached_jwks = None

def get_jwks():
    """Fetch and cache the JWKS (JSON Web Key Set) from Supabase"""
    global _cached_jwks
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    
    if _cached_jwks is None:
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        response = requests.get(jwks_url)
        
        if response.status_code != 200:
            raise Exception(f"Could not fetch JWKS, status code: {response.status_code}")
        
        _cached_jwks = response.json()
    
    return _cached_jwks


def verify_supabase_token_payload(token: str):
    """Verify a Supabase JWT token using the JWKS endpoint"""
    try:
        # 1. Get the 'kid' (Key ID) from the header without verifying yet
        headers = jwt.get_unverified_headers(token)
        kid = headers.get('kid')
        
        if not kid:
            raise HTTPException(status_code=401, detail="Missing kid in header")
        
        # 2. Get the public keys
        jwks = get_jwks()
        
        # 3. Find the specific key that matches the token's kid
        key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
        
        if not key:
            raise HTTPException(status_code=401, detail="RSA public key not found")
        
        # 4. Pass the raw 'key' dict directly to jwt.decode
        # The library handles the conversion from JWK internally
        # Use the algorithm specified in the key
        key_alg = key.get('alg', 'RS256')
        payload = jwt.decode(
            token,
            key,
            algorithms=[key_alg],
            audience="authenticated"
        )
        
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"JWT Validation Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


async def verify_supabase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # This extract the "Bearer <token>" string
    token = credentials.credentials
    payload = verify_supabase_token_payload(token)
    return payload


async def get_current_active_user(payload: dict = Depends(verify_supabase_token)):
    # Simply return the payload which contains user info (sub, email, etc.)
    return payload