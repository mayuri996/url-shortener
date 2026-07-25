from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
app=FastAPI()

#request model to convert json to python object
class UrlRequest(BaseModel):
    url:str


#stores mapping of code to long _url
#this is a python dictionary similar to hash map in c++
url_database={}

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

#this api returns a shortened code
#call it when long url needs to be converted to short url
@app.post('/shorten')
def shortenUrl(request:UrlRequest):
    long_url=request.url
    code=generateShortCode(long_url)
    
    short_url=f"http://127.0.0.1:8000/{code}"

    #doesnt matter how we store it
    saveUrl(long_url,code)

    return {
        "short_url":short_url
    }

#this api redirects to the long url using the short url code
@app.get("/{short_code}")
def redirectUrl(short_code:str):
    #doesnt matter where it comes from
    long_url=getLongUrl(short_code)
    return RedirectResponse(long_url)

#this fn generates a short code for the given long url
#it uses polynomial hashing
def generateShortCode(long_url:str):
    hash_value=0
    base=131
    MOD=1000000007

    #convert long_url to a polynomial hash
    for c in long_url:
        val=ord(c)
        hash_value=(hash_value*base+val)%MOD

    return str(hash_value)

#stores the long_url and its code in storage
def saveUrl(long_url:str,code:str):
    url_database[code]=long_url

#retrieves the long_url and its code from storage
def getLongUrl(code:str):
    return url_database[code]