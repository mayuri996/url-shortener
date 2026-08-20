import {useState} from 'react';
import {NavLink} from 'react-router-dom';

function Register(){
    const [userEmail,setUserEmail]=useState("")
    const [userPassword,setUserPassword]=useState("")
    const [userName,setUserName]=useState("")
    const [isRegistered, setIsRegistered]=useState(false)
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL
    async function handleSignUp(){
        setIsRegistered(false);
        //handle network errors
        try {
            const  response=await fetch(`${BACKEND_URL}/register`,{
                "method":"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    email:userEmail,
                    user_name:userName,
                    password:userPassword
                })
            })

            const result=await response.json()
            
            //handle error messages
            if (!response.ok) {
                if (typeof result.detail=="string"){
                    alert(result.detail)
                }
                else{
                    alert(result.detail[0].msg)
                }
                return;
            }
            
            //if registered successfully 
            setIsRegistered(true);

        }
        catch(error){
            alert("Unable to connect to the server. Please try again.")
            return;
        }
        
    }
    return (
        <div>
            <nav className="navbar">
                <NavLink className={({isActive})=> isActive ? "active-link":"nav-link"}to="/login">Login</NavLink>
                {" | "}
                <NavLink className={({isActive})=> isActive ? "active-link":"nav-link"}  to="/signup">Register</NavLink>
            </nav>
        <h1>Sign Up</h1>
        <input
        className="input"
        type="text"
        placeholder="Enter your username"
        value={userName}
        onChange={(e)=>setUserName(e.target.value)}
        required/>
        <br></br>
        <br></br>
        <input
        className="input"
        type="email"
        placeholder="Enter your email"
        value={userEmail}
        onChange={(e)=>setUserEmail(e.target.value)}
        required/>
        <br></br>
        <br></br>
        <input
        className="input"
        type="password"
        placeholder="Enter your password"
        value={userPassword}
        onChange={(e)=>setUserPassword(e.target.value)}
        required/>
        <br></br>
        <br></br>
        <button
        className="click-button" 
        onClick={handleSignUp}
        >Sign Up</button>
        {isRegistered && (
            <p>Registered Successfully</p>
        )}
        </div>

        
    )
}

export default Register