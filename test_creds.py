from main_fastapi import check_creds
import asyncio
from fastapi.security import HTTPBasicCredentials

def test_auth():
    res = asyncio.run(check_creds(HTTPBasicCredentials(username="fail", password="invalid")))
    assert 0, res
    

