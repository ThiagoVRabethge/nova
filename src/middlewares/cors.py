from decouple import config
from fastapi.middleware.cors import CORSMiddleware


def cors(app):
    origins = [
        config("CLIENT_URL"),
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
