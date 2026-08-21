from fastapi.testclient import TestClient
from main import app,BASE_URL,rate_limit_store,cursor,conn
import pytest

client=TestClient(app)

@pytest.fixture(autouse=True)
def reset_test_state():
    #reset rate limiter,user, url records , and cookies before each test
    rate_limit_store.clear()
    cursor.execute("DELETE FROM URLS")
    cursor.execute("DELETE FROM USERS")
    client.cookies.clear()
    conn.commit()

def test_home():
    response=client.get("/")

    assert response.status_code==200

    assert response.json()=={
        "message":"Backend is working"
    }

def test_shorten_url():
    #register
    register_response=client.post("/register",json={
        "email":"login@example.com",
        "user_name":"string",
        "password":"string"
    })
    
    assert register_response.status_code==200

    #login
    login_response=client.post("/login",json={
        "email":"login@example.com",
        "password":"string"
    })

    assert login_response.status_code==200

    assert "access_token" in login_response.cookies

    #shorten
    shorten_response=client.post("/shorten",json={
        "url":"https://test-shorten-url.com"
    })

    assert shorten_response.status_code==200

    data=shorten_response.json()

    assert "short_url" in data

    assert data["short_url"].startswith(f"{BASE_URL}/")

def test_shorten_redirect_url():
    #register
    register_response=client.post("/register",json={
        "email":"login@example.com",
        "user_name":"string",
        "password":"string"
    })
    
    assert register_response.status_code==200

    #login
    login_response=client.post("/login",json={
        "email":"login@example.com",
        "password":"string"
    })

    assert login_response.status_code==200

    assert "access_token" in login_response.cookies

    #shorten
    shorten_response=client.post("/shorten",json={
        "url":"https://test-shorten-url.com"
    })

    assert shorten_response.status_code==200

    data=shorten_response.json()

    assert "short_url" in data

    assert data["short_url"].startswith(f"{BASE_URL}/")

    short_url=data["short_url"]

    parts=short_url.split('/')

    code=parts[-1]

    #redirect

    redirect_response=client.get(f"/{code}",follow_redirects=False)

    assert redirect_response.status_code==307

def test_shorten_stats():
    #register
    register_response=client.post("/register",json={
        "email":"login@example.com",
        "user_name":"string",
        "password":"string"
    })
    
    assert register_response.status_code==200

    #login
    login_response=client.post("/login",json={
        "email":"login@example.com",
        "password":"string"
    })

    assert login_response.status_code==200

    assert "access_token" in login_response.cookies

    #shorten
    shorten_response=client.post("/shorten",json={
        "url":"http://test-shorten-stats.com"
    })

    assert shorten_response.status_code==200

    data=shorten_response.json()

    assert "short_url" in data

    assert data["short_url"].startswith(f"{BASE_URL}/")

    short_url=data["short_url"]

    parts=short_url.split('/')

    code=parts[-1]

    #stats
    stats_response=client.get(f"/stats/{code}")

    assert stats_response.status_code==200

    stats_response_data=stats_response.json()

    assert stats_response_data["click_count"]==0
    assert stats_response_data["long_url"]=="http://test-shorten-stats.com/"
    assert "created_at" in stats_response_data
    assert "last_clicked_at" in stats_response_data

def test_shorten_redirect_stats():
    #register
    register_response=client.post("/register",json={
        "email":"login@example.com",
        "user_name":"string",
        "password":"string"
    })
    
    assert register_response.status_code==200

    #login
    login_response=client.post("/login",json={
        "email":"login@example.com",
        "password":"string"
    })

    assert login_response.status_code==200

    assert "access_token" in login_response.cookies

    #shorten
    shorten_response=client.post("/shorten",json={
        "url":"https://test-shorten-redirect-stats.com"
    })

    assert shorten_response.status_code==200

    data=shorten_response.json()

    assert "short_url" in data

    assert data["short_url"].startswith(f"{BASE_URL}/")

    short_url=data["short_url"]

    parts=short_url.split('/')

    code=parts[-1]

    #redirect

    redirect_response=client.get(f"/{code}",follow_redirects=False)

    assert redirect_response.status_code==307

    #stats

    stats_response=client.get(f"/stats/{code}")
    assert stats_response.status_code==200
    stats_response_data=stats_response.json()

    assert stats_response_data["click_count"]==1
    assert stats_response_data["long_url"]=="https://test-shorten-redirect-stats.com/"
    assert "created_at" in stats_response_data
    assert "last_clicked_at" in stats_response_data

def test_rate_limit():
    #register
    register_response=client.post("/register",json={
        "email":"login@example.com",
        "user_name":"string",
        "password":"string"
    })
    
    assert register_response.status_code==200

    #login
    login_response=client.post("/login",json={
        "email":"login@example.com",
        "password":"string"
    })

    assert login_response.status_code==200


    assert "access_token" in login_response.cookies

    #rate limit verify
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

    assert "access_token" in login_response.cookies

def test_authentication():
    auth_response=client.post("/shorten",json={
        "url":"https://example.com"
    })

    assert auth_response.status_code==401

def test_authorization():
    #Test that 2 different users should not be able to access each other's short urls
    #Register both users
    register_user_A=client.post("/register",json={
        "email":"usera@example.com",
        "user_name":"usera",
        "password":"string"
    })

    assert register_user_A.status_code==200

    register_user_B=client.post("/register",json={
        "email":"userb@example.com",
        "user_name":"userb",
        "password":"string"
    })

    assert register_user_B.status_code==200

    #Login user A
    login_user_A=client.post("/login",json={
        "email":"usera@example.com",
        "password":"string"
    })

    assert login_user_A.status_code==200

    assert "access_token" in login_user_A.cookies

    #create short url through user A account

    shorten_url_user_A=client.post("/shorten",json={
        "url":"http://test-shorten-url-user-A.com,"
    })

    assert shorten_url_user_A.status_code==200

    data_user_A=shorten_url_user_A.json()
    
    assert "short_url" in data_user_A

    assert data_user_A["short_url"].startswith(f"{BASE_URL}/")

    short_url_user_A=data_user_A["short_url"]

    parts=short_url_user_A.split("/")

    code=parts[-1]

    #Try to check stats for short url created by user A when user A logged in

    print(code)

    check_stats=client.get(f"/stats/{code}")

    assert check_stats.status_code==200

    #clear user A session

    client.cookies.clear()

    #Login user b
    login_user_B=client.post("/login",json={
        "email":"userb@example.com",
        "password":"string"
    })

    assert login_user_B.status_code==200

    assert "access_token" in login_user_B.cookies

    #Try to check stats for short url created by user A when user B logged in

    check_stats=client.get(f"/stats/{code}")

    assert check_stats.status_code==404

