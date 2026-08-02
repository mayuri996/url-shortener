from fastapi.testclient import TestClient
from main import app

client=TestClient(app)

def test_home():
    response=client.get("/")

    assert response.status_code==200

    assert response.json()=={
        "message":"Backend is working"
    }

def test_shorten_url():
    response=client.post("/shorten",json={
        "url":"https://google.com"
    })

    assert response.status_code==200

    data=response.json()

    assert "short_url" in data

    assert data["short_url"].startswith("http://127.0.0.1:8000/")

def test_shorten_redirect_url():
    shorten_response=client.post("/shorten",json={
            "url":"http://g.com"
        })
    
    assert shorten_response.status_code==200

    data=shorten_response.json()

    assert "short_url" in data

    assert data["short_url"].startswith("http://127.0.0.1:8000/")

    short_url=data["short_url"]

    parts=short_url.split('/')

    code=parts[-1]

    redirect_response=client.get(f"/{code}",follow_redirects=False)

    assert redirect_response.status_code==307
