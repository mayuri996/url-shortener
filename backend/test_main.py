from fastapi.testclient import TestClient
from main import app,BASE_URL,rate_limit_store,cursor,conn
import pytest

client=TestClient(app)

@pytest.fixture(autouse=True)
def reset_test_state():
    #reset rate limiter,users, and url records before each test
    rate_limit_store.clear()
    cursor.execute("DELETE FROM URLS")
    cursor.execute("DELETE FROM USERS")

    conn.commit()

def test_home():
    response=client.get("/")

    assert response.status_code==200

    assert response.json()=={
        "message":"Backend is working"
    }

def test_shorten_url():
    response=client.post("/shorten",json={
        "url":"https://test-shorten-url.com"
    })

    assert response.status_code==200

    data=response.json()

    assert "short_url" in data

    assert data["short_url"].startswith(f"{BASE_URL}/")

def test_shorten_redirect_url():
    shorten_response=client.post("/shorten",json={
        "url":"http://test-shorten-redirect-url.com"
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
        "url":"http://test-shorten-stats.com"
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
    assert stats_response_data["long_url"]=="http://test-shorten-stats.com/"
    assert "created_at" in stats_response_data
    assert "last_clicked_at" in stats_response_data

def test_shorten_redirect_stats():
    shorten_response=client.post("/shorten",json={
        "url":"http://test-shorten-redirect-stats.com"
    })

    assert shorten_response.status_code==200

    shorten_response_data=shorten_response.json()

    assert "short_url" in shorten_response_data
    assert shorten_response_data["short_url"].startswith(f"{BASE_URL}/")
    
    short_url=shorten_response_data["short_url"]

    parts=short_url.split('/')
    
    code=parts[-1]
    
    redirect_response=client.get(f"/{code}",follow_redirects=False)

    assert redirect_response.status_code==307

    stats_response=client.get(f"/stats/{code}")
    assert stats_response.status_code==200
    stats_response_data=stats_response.json()

    assert stats_response_data["click_count"]==1
    assert stats_response_data["long_url"]=="http://test-shorten-redirect-stats.com/"
    assert "created_at" in stats_response_data
    assert "last_clicked_at" in stats_response_data

def test_rate_limit():
    for i in range(5):
        response=client.post("/shorten",json={
            "url":"https://test-rate-limit.com"
        })

        assert response.status_code==200

    response=client.post("/shorten",json={
        "url":"https://test-rate-limit.com"
    })

    assert response.status_code==429

def test_register_user():
    register_response=client.post("/register",json={
        "email":"user@example.com",
        "user_name":"string",
        "password":"string"
    })

    assert register_response.status_code==200

def test_login_user():
    register_response=client.post("/register",json={
            "email":"login@example.com",
            "user_name":"string",
            "password":"string"
        })
    
    assert register_response.status_code==200

    login_response=client.post("/login",json={
        "email":"login@example.com",
        "password":"string"
    })

    assert login_response.status_code==200

    login_response_data=login_response.json()

    assert "access_token" in login_response_data
    assert login_response_data["token_type"]=="bearer"

