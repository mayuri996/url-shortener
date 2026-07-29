from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from fastapi.responses import RedirectResponse
import sqlite3
app=FastAPI()

#validate the url 
class UrlRequest(BaseModel):
    url:HttpUrl


#stores mapping of code to long _url
conn=sqlite3.connect("url_shortener.db",check_same_thread=False)
cursor=conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS urls(" \
"id INTEGER PRIMARY KEY AUTOINCREMENT, " \
"code TEXT UNIQUE," \
"long_url TEXT NOT NULL)")
conn.commit()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
def shortenUrl(request:UrlRequest):
    long_url=str(request.url)

    code=getCodeForUrl(long_url)

    if code is None:
        #doesnt matter how we store it
        code=saveUrl(long_url)
        
    short_url=f"http://127.0.0.1:8000/{code}"

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
    return RedirectResponse(long_url)

#stores the long_url and its code in storage
def saveUrl(long_url:str):

    #first insert in storage
    #then use the last inserted id to generate base62 encoding
    #then update the row with the code
    #and return the code

    cursor.execute("INSERT INTO urls (" \
    "long_url) " \
    "VALUES (?)",(long_url,))

    url_id=cursor.lastrowid
    code=encodeBase62(url_id)
    cursor.execute("UPDATE urls " \
    "SET code=? " \
    "WHERE id=?",(code,url_id))
    conn.commit()

    return code


#retrieves the long_url from storage
def getLongUrl(code:str):
    cursor.execute("SELECT long_url " \
    "FROM urls " \
    "WHERE code=?",(code,))

    row=cursor.fetchone()
    if row is None:
        return None
    return row[0]


#retrieves the code for a given long url
def getCodeForUrl(long_url:str):
    cursor.execute("SELECT code " \
    "FROM urls " \
    "WHERE long_url=?",(long_url,))

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




