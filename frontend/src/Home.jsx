import { useState } from 'react';
import {NavLink} from "react-router-dom";
import './App.css'

function App() {
  const [url,setUrl]=useState("")
  const [shortUrl,setShortUrl]=useState("")
  const BACKEND_URL=import.meta.env.VITE_BACKEND_URL
  const [loading,setLoading]=useState(false)
  async function  handleShortenUrl(){
    setLoading(true);
    setShortUrl("");
    //handle network errors
    try {
      const response=await fetch(`${BACKEND_URL}/shorten`,{
        "method":"POST",
        headers:{
          "Content-Type":"application/json"
        },
        body:JSON.stringify({url})}
      );

      const result=await response.json();
      if (response.ok) setShortUrl(result.short_url);
      else if (typeof result.detail=="string"){
        alert(result.detail);
      }
      else alert(result.detail[0].msg);
    }
    catch (error) {
      alert("Unable to connect to the server. Please try again.");
    }
    setLoading(false);
    
  }
  return (
    <div>
      <nav className="navbar">
        <NavLink className={({isActive})=>isActive ? "active-link":"nav-link"}  to="/">Home</NavLink> 
        {" | "}
        <NavLink  className={({isActive})=>isActive ? "active-link":"nav-link"} to="/analytics">Analytics</NavLink>
      </nav>
      <br></br>
      <h1>URL Shortener</h1>
    <input
    className="url-input"
    type="text"
    placeholder="Enter URL"
    value={url}
    onChange={(e)=>setUrl(e.target.value)}
    />
    <br></br>
    <br></br>

    <button 
    className="click-button"
    onClick={handleShortenUrl}>Shorten URL</button>
    {loading && (
      <p>Generating short URL...</p>
    )}
    {shortUrl && !loading && (
      <p className="display-info">Shortened URL : <a 
      href={shortUrl}
      target="_blank"
      rel="noopener noreferrer"> {shortUrl}
      </a>
      </p>
      )
    }
    </div>

    
  )
}

export default App
