from fastapi import FastAPI,HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from fastapi.responses import RedirectResponse
import psycopg
import os
from dotenv import load_dotenv
import time

app=FastAPI()
load_dotenv()
BASE_URL=os.getenv("BASE_URL")
FRONTEND_URL=os.getenv("FRONTEND_URL")

RATE_LIMIT=5
WINDOW_SECONDS=60
rate_limit_store={}
#validate the url 
class UrlRequest(BaseModel):
    url:HttpUrl

#stores mapping of code to long_url
conn=psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cursor=conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS urls(" \
"id SERIAL PRIMARY KEY, " \
"code TEXT UNIQUE," \
"long_url TEXT NOT NULL," \
"click_count INTEGER NOT NULL DEFAULT 0, " \
"created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
conn.commit()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get('/')
def home():
    return{
        "message":"Backend is working"
    }

#this api returns a shortened url
#call it when long url needs to be converted to short url
@app.post('/shorten')
def shortenUrl(request:Request,url_request:UrlRequest):
    long_url=str(url_request.url)
    client_ip=request.client.host

    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    code=getCodeForUrl(long_url)

    if code is None:
        code=saveUrl(long_url)
        
    short_url=f"{BASE_URL}/{code}"

    return {
        "short_url":short_url
    }
    

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

    #update click count
    updateClickCount(short_code)
    return RedirectResponse(
        url=long_url,
        status_code=307)

#this api returns number of times a short url was clicked
@app.get("/stats/{short_code}")
def getAnalytics(short_code:str):
    stats=getStats(short_code)

    #if given short url does not exist, return 404
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found"
        )

    clicks=stats[0]
    created_at=stats[1]
    long_url=stats[2]

    return {
        "click_count":clicks,
        "created_at":created_at,
        "long_url":long_url
    }


#stores the long_url and its code in storage
def saveUrl(long_url:str):

    #first add long_url in urls
    #then use the last inserted id to encode long_url to base62 
    #then update the row with the code
    #and then return the code

    cursor.execute("INSERT INTO urls (" \
    "long_url, created_at) " \
    "VALUES (%s,NOW()) " \
    "RETURNING id",
    (long_url,))

    url_id=cursor.fetchone()[0]

    #encode based on auto increment id
    code=encodeBase62(url_id)

    #update the code
    cursor.execute("UPDATE urls " \
    "SET code=%s " \
    "WHERE id=%s",(code,url_id))

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


#retrieves the code for a given long url
def getCodeForUrl(long_url:str):
    cursor.execute("SELECT code " \
    "FROM urls " \
    "WHERE long_url=%s",(long_url,))

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

def updateClickCount(code:str):
    cursor.execute("UPDATE urls " \
    "SET click_count=click_count+1 " \
    "WHERE code=%s",(code,))
    conn.commit()

def getStats(code:str):
    cursor.execute("SELECT click_count, "\
    "to_char(created_at, 'dd Mon YYYY HH24:MI:SS OF') as created_at, long_url    " \
    "FROM urls " \
    "WHERE code=%s",(code,))

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
