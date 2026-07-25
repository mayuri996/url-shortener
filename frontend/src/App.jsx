import { useState } from 'react'
import './App.css'

function App() {
  const [url,setUrl]=useState("")
  const [shortUrl,setShortUrl]=useState("")
  async function  handleShortenUrl(){
    const response=await fetch("http://127.0.0.1:8000/shorten",{"method":"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({url})}
    )

    const result=await response.json();
    setShortUrl(result.short_url);
  }
  return (
    <div>
      <h1>Url Shortener</h1>
    <input
    type="text"
    placeholder="Enter URL"
    value={url}
    onChange={(e)=>setUrl(e.target.value)}
    />

    <button onClick={handleShortenUrl}>Shorten URL</button>

    <p>Shortened Url: {shortUrl}</p>
    </div>

    
  )
}

export default App
