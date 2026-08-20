import {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {NavLink} from 'react-router-dom';

function Login(){
    const [userEmail,setUserEmail]=useState("")
    const [userPassword,setUserPassword]=useState("")
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL
    const [isLoggedIn,setIsLoggedIn]=useState(false)
    const navigate=useNavigate();
    async function handleLogin(){
        setIsLoggedIn(false)
        try{
            const response = await fetch(`${BACKEND_URL}/login`,{
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    email:userEmail,
                    password:userPassword
                })
            })

            const result=await response.json()

            if (!response.ok){
                if (typeof result.detail=="string"){
                    alert(result.detail)
                    return;
                }
                alert(result.detail[0].msg)
                return;
            }
            
            //if successfully logged in 
            //store token in session storage
            sessionStorage.setItem("access_token",result.access_token)
            setIsLoggedIn(true)
            navigate("/")
        }
        catch (error){
            console.log(error)
            alert("Unable to connect to server. Please try again.")
        }
        
    }
    return (
        <div>
            <nav className="navbar">
                <NavLink className={({isActive})=> isActive ? "active-link":"nav-link"}to="/login">Login</NavLink>
                {" | "}
                <NavLink className={({isActive})=> isActive ? "active-link":"nav-link"}  to="/signup">Register</NavLink>
            </nav>
            <h1>Login</h1>

            <input
            className="input"
            type="email"
            placeholder="Enter your email"
            value={userEmail}
            onChange={(e)=>setUserEmail(e.target.value)}/>
            <br></br>
            <br></br>

            <input
            className="input"
            type="password"
            placeholder="Enter your password"
            value={userPassword}
            onChange={(e)=>setUserPassword(e.target.value)}/>

            <br></br>
            <br></br>

            <button className="click-button"
            onClick={handleLogin}>Login</button>

            {isLoggedIn && (
                <p>Logged in successfully.</p>
            )}
        </div>
        
    )
}

export default Login