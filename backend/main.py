from fastapi import FastAPI,HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, EmailStr
from fastapi.responses import RedirectResponse
import psycopg
import os
from dotenv import load_dotenv
import time
import bcrypt
import jwt
import datetime
from datetime import timezone,timedelta,datetime
from fastapi import Depends

app=FastAPI()
load_dotenv()

BASE_URL=os.getenv("BASE_URL")
FRONTEND_URL=os.getenv("FRONTEND_URL")

RATE_LIMIT=5
WINDOW_SECONDS=60
rate_limit_store={}

JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=timedelta(minutes=15)
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")

#validate the url 
class validUrl(BaseModel):
    url:HttpUrl
#define model for user register
class UserRegister(BaseModel):
    email:EmailStr
    user_name:str
    password:str

#define model for user login
class UserLogin(BaseModel):
    email:EmailStr
    password:str

#model for jwt token
class JWTToken(BaseModel):
    access_token:str
    token_type:str

#stores mapping of code to long_url
conn=psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cursor=conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(" \
"user_id SERIAL PRIMARY KEY, " \
"email TEXT UNIQUE NOT NULL, " \
"user_name TEXT NOT NULL, " \
"password_hash TEXT NOT NULL )")

cursor.execute("CREATE TABLE IF NOT EXISTS urls(" \
"url_id SERIAL PRIMARY KEY, " \
"code TEXT UNIQUE," \
"long_url TEXT NOT NULL," \
"click_count INTEGER NOT NULL DEFAULT 0, " \
"created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), " \
"last_clicked_at TIMESTAMPTZ, " \
"user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE)")

conn.commit()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#Dependencies
def verify_user(request:Request):
    #1. Check if token is valid
    #2. Decode the token
    #3. Extract user_id from it
    #4. Return the user_id of the verified user
    authorization=request.headers.get("Authorization")

    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    auth_token=authorization.split(" ")

    if len(auth_token)!=2 or auth_token[0]!="Bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    token_value=auth_token[1]

    payload=decode_jwt_access_token(token_value)

    user_id=payload["sub"]

    return int(user_id)


# API end points
@app.get('/')
def home():
    return{
        "message":"Backend is working"
    }

#this api returns a shortened url
#Return a short url for a given long url and user id
@app.post('/shorten')
def shortenUrl(request:Request,valid_url:validUrl,user_id=Depends(verify_user)):
    #1. Check if the ip is rate limited
    #2. If short code exists for the long url and the given user id, return the short url
    #3. Else create the short code for the user id, and return the short url

    long_url=str(valid_url.url)
    client_ip=request.client.host

    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    code=getCodeForUrl(long_url,user_id)

    if code is None:
        code=saveUrl(long_url,user_id)
        
    short_url=f"{BASE_URL}/{code}"

    return {
        "short_url":short_url
    }
    
#this api returns number of times a short url was clicked
@app.get("/stats/{short_code}")
def getAnalytics(short_code:str, user_id=Depends(verify_user)):
    stats=getStats(short_code,user_id)

    #if given short url does not exist for the given user id, return 404
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    clicks=stats[0]
    created_at=stats[1]
    last_clicked_at=stats[2]
    long_url=stats[3]

    return {
        "click_count":clicks,
        "created_at":created_at,
        "last_clicked_at":last_clicked_at,
        "long_url":long_url
    }

#define register endpoint
@app.post("/register")
def registerUser(user: UserRegister):
    status=saveUser(user)

    if status is True:
        return {
            "message":"User created successfully."
        }

    else:
        raise HTTPException(
            status_code=409,
            detail="User already exists")
    
#define login endpoint
@app.post("/login")
def loginUser(user:UserLogin):
    email=user.email
    password=user.password
    password_hash=findUser(email)

    if password_hash is None:
        #TODO: handle return
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_match=verify_password(password,password_hash)

    if not password_match:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    #generate jwt token
    user_id=findUserId(email)
    token_expiry_time=datetime.now(timezone.utc)+JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    payload={"sub":str(user_id),"exp":token_expiry_time}

    jwt_access_token=create_jwt_access_token(payload)

    return JWTToken(access_token=jwt_access_token, token_type="bearer")

#this api redirects to the long url using the short url code
@app.get("/{short_code}")
def redirectUrl(short_code:str):
    #doesnt matter where it comes from
    long_url=getLongUrl(short_code)
    if long_url is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    updateStats(short_code)
    return RedirectResponse(
        url=long_url,
        status_code=307)

#stores the long_url and its code in storage
def saveUrl(long_url:str,user_id:int):

    #1. Add long_url in urls for the given user id
    #2. Use the last inserted id to encode long_url to base62 
    #3. Update the row with the code
    #4. Return the code


    cursor.execute("INSERT INTO urls (" \
    "long_url, created_at,user_id) " \
    "VALUES (%s,NOW(),%s) " \
    "RETURNING url_id",
    (long_url,user_id))

    url_id=cursor.fetchone()[0]

    #encode based on auto increment id
    code=encodeBase62(url_id)

    #update the code
    cursor.execute("UPDATE urls " \
    "SET code=%s " \
    "WHERE url_id=%s",(code,url_id))

    #commit only after insert and update
    conn.commit()

    return code


#retrieves the long_url from storage
def getLongUrl(code:str):
    cursor.execute("SELECT long_url " \
    "FROM urls " \
    "WHERE code=%s",(code,))

    row=cursor.fetchone()
    if row is None:
        return None
    return row[0]


#retrieves the code for a given long url and user id
def getCodeForUrl(long_url:str,user_id:int):
    cursor.execute("SELECT code " \
    "FROM urls " \
    "WHERE long_url=%s " \
    "AND user_id=%s",(long_url,user_id))

    row=cursor.fetchone()

    if row is None:
        return None

    return row[0]

def encodeBase62(url_id:int):
    num=url_id
    answer=""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    base=62

    while(num>0):
        remainder=num%base
        answer+=chars[remainder]
        num//=base  

    #reverse the string
    answer=answer[::-1]

    return answer

def updateStats(code:str):
    cursor.execute("UPDATE urls " \
    "SET click_count=click_count+1, " \
    "last_clicked_at=NOW() " \
    "WHERE code=%s",(code,))
    conn.commit()

def getStats(code:str,user_id:int):
    cursor.execute("SELECT click_count, "\
    "to_char(created_at, 'dd Mon YYYY HH24:MI:SS OF') as created_at, " \
    "to_char(last_clicked_at,'dd Mon YYYY HH24:MI:SS OF') as last_clicked_at, " \
    "long_url    " \
    "FROM urls " \
    "WHERE code=%s " \
    "AND user_id=%s",(code,user_id))

    row=cursor.fetchone()

    if row is None:
        return None

    return row

#protects shorten url endpoint from getting more than 5 requests within 60 seconds in the same process
def is_rate_limited(ip):
    current_time=time.time()
    if ip not in rate_limit_store:
        rate_limit_store[ip]={
            "count":1,
            "window_start":current_time
        }
        return False
    record=rate_limit_store[ip]
    elapsed_time=current_time-record["window_start"]

    if elapsed_time>=WINDOW_SECONDS:
        record["count"]=1
        record["window_start"]=current_time
        return False

    if record["count"]>=RATE_LIMIT:
        return True
    record["count"]+=1
    return False

def hash_password(password:str):
    salt=bcrypt.gensalt()
    byte_password=password.encode("utf-8")
    hashed=bcrypt.hashpw(byte_password,salt)
    return hashed.decode("utf-8")

def saveUser(user:UserRegister):
    #1. First check if user already exists in db
    #2. Return false when user already exist
    #3. Else, hash user's password
    #3. Save new user with hashed password
    email=user.email
    user_name=user.user_name
    password=user.password

    cursor.execute("SELECT user_id " \
    "FROM users " \
    "WHERE email=%s",(email,))

    row=cursor.fetchone()
    
    if row is not None:
        return False

    password_hash=hash_password(password)

    cursor.execute("INSERT INTO users(" \
    "email,user_name,password_hash) " \
    "VALUES (%s,%s,%s)",(email,user_name,password_hash))
    conn.commit()

    return True


def findUser(email:str):
    #If user registered, then return email id
    #Else user does not exist, so they are not registered
    cursor.execute("SELECT password_hash " \
    "FROM users " \
    "WHERE email=%s",(email,))

    row=cursor.fetchone()

    #return none if user not registered
    if row is None:
        return None

    password_hash=row[0]

    return password_hash

def verify_password(password:str,password_hash:str):
    #Check if the password matches the stored password_hash
    #use bcrypt to hash password and check against stored password_hash
    #if not match, then return false
    #else return true
    byte_curr_password=password.encode("utf-8")
    byte_password_hash=password_hash.encode("utf-8")

    #return true if password is correct, else return false
    password_match= bcrypt.checkpw(byte_curr_password,byte_password_hash)

    if not password_match:
        return False

    return True

#this function creates a jwt access token for a given payload and timedelta
def create_jwt_access_token(payload:dict):

    encoded_jwt_token=jwt.encode(payload,JWT_SECRET_KEY,JWT_ALGORITHM)

    return encoded_jwt_token


def findUserId(email:str):
    #Find user id by email
    #If not found, then user does not exist
    cursor.execute("SELECT user_id " \
    "FROM users " \
    "WHERE email=%s",(email,))

    row=cursor.fetchone()

    if row is None:
        return None

    user_id=row[0]

    return user_id

def decode_jwt_access_token(token:str):
    try:
        decoded_jwt_token=jwt.decode(token,JWT_SECRET_KEY,JWT_ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return decoded_jwt_token