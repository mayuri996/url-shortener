from fastapi.testclient import TestClient
from main import app,BASE_URL

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

    assert data["short_url"].startswith(f"{BASE_URL}/")

def test_shorten_redirect_url():
    shorten_response=client.post("/shorten",json={
        "url":"http://google.com"
    })
    
    assert shorten_response.status_code==200

    data=shorten_response.json()

    assert "short_url" in data

    assert data["short_url"].startswith(f"{BASE_URL}/")

    short_url=data["short_url"]

    parts=short_url.split('/')

    code=parts[-1]

    redirect_response=client.get(f"/{code}",follow_redirects=False)

    assert redirect_response.status_code==307

def test_shorten_stats():
    shorten_response=client.post("/shorten",json={
        "url":"http://github.com"
    })
        
    assert shorten_response.status_code==200

    shorten_response_data=shorten_response.json()

    assert "short_url" in shorten_response_data

    assert shorten_response_data["short_url"].startswith(f"{BASE_URL}/")

    short_url=shorten_response_data["short_url"]

    parts=short_url.split('/')

    code=parts[-1]

    stats_response=client.get(f"/stats/{code}")

    assert stats_response.status_code==200

    stats_response_data=stats_response.json()

    assert stats_response_data["click_count"]==0
    assert stats_response_data["long_url"]=="http://github.com/"