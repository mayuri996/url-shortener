import { useState } from 'react';
import { NavLink } from "react-router-dom";
function Analytics(){
    const [clickCount,setClickCount]=useState("");
    const [longUrl,setLongUrl]=useState("");
    const [shortUrl,setShortUrl]=useState("");
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const URL_PREFIX=`${BACKEND_URL}/`;
    async function handleGetStats(){
        //handle network errors
        try{
            //first check if it is a valid short url
            //then, extract the code from the url
            
            if (!shortUrl.startsWith(URL_PREFIX)){
                alert("Please enter a valid short URL.");
                return;
            }
            
            const shortCode=shortUrl.substring(URL_PREFIX.length);
            
            const response=await fetch(`${BACKEND_URL}/stats/${shortCode}`,{
                "method":"GET",
                headers:{
                    "Content-Type":"application/json"
                }
            });
            
            const result=await response.json();

            if (response.ok){
                setClickCount(result.click_count);
                setLongUrl(result.long_url);
            }
            else{
                alert(result.detail);
            }
            
        }
        catch (e){
            alert("Unable to connect to the server. Please try again.");
        }
    }
    return (
        <div>

            <nav>
                <NavLink to="/">Home</NavLink>
                {" | "}
                <NavLink to="/analytics">Analytics</NavLink>
            </nav>
            <h1>Analytics</h1>
            <input
            type="text" 
            placeholder="Enter short url" 
            value={shortUrl}
            onChange={(e)=>setShortUrl(e.target.value)}/>
            
            <button onClick={handleGetStats}>Get Analytics</button>

            {clickCount!=="" && <p>Short URL: {shortUrl}</p>}
            {clickCount && <p>Click Count: {clickCount}</p>}
            {longUrl && <p>Original URL: {longUrl}</p>}
        </div>
    );
}

export default Analytics