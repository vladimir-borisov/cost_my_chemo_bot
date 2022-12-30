import httpx

payload = {
    "update_id": 216382381,
    "message": {
        "message_id": 621,
        "from": {
            "id": 130909778,
            "is_bot": False,
            "first_name": "Fiodor",
            "last_name": "Yeremeev",
            "username": "yaevak",
            "language_code": "en",
        },
        "chat": {
            "id": 130909778,
            "first_name": "Fiodor",
            "last_name": "Yeremeev",
            "username": "yaevak",
            "type": "private",
        },
        "date": 1672398044,
        "text": "190",
    },
}
resp = httpx.post("http://0.0.0.0:8080", json=payload)
print(resp.json())
