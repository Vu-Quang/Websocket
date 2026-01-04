import os

ENV = os.getenv("ENV", "dev")

if ENV == "dev":
    CORS_CONFIG = {
        "allow_origins": ["*"],
        "allow_credentials": False,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
else:
    CORS_CONFIG = {
        "allow_origins": [
            "https://pos.yourcompany.vn",
            "https://admin.yourcompany.vn",
        ],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
        ],
    }
