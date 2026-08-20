import { Routes, Route } from "react-router-dom"
import Home from "./Home"
import Analytics from "./Analytics"
import Register from "./Register"
import Login from "./Login"

function App(){
  return (
    <Routes>
      <Route path="/" element={<Home/>} />
      <Route path="/analytics" element={<Analytics/>}/>
      <Route path="/signup" element={<Register/>}/>
      <Route path="/login" element={<Login/>}/>
    </Routes>
  )
}
export default App;