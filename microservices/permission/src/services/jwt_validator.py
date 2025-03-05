from jose import JWTError, jwt

class JWTValidator:
    def __init__(self,  refresh_interval=3600):
        self.public_key = None
        self.refresh_interval = refresh_interval
        
    async def verify_token(self, token: str):
        public_key = self.public_key
        if not public_key:
            return False
        try:
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except JWTError:
            return False
