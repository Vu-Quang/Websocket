import jwt
from datetime import datetime, timedelta
SECRET = "SECRET123"
ALGO = "HS256"

def generate_ws_token(order_id):
    payload = {
        "order_id": order_id,
        "exp": datetime.now() + timedelta(minutes=15)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


print(generate_ws_token("order_123"))