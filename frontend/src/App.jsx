import { BrowserRouter, Routes, Route } from "react-router-dom"
import { useState, useEffect } from "react"

import './App.css'

import { IntroAnimation } from "./components/IntroAnimation"
import Home from "./pages/Home"

function App() {
  const[showIntro, setShowIntro] = useState(true)

   useEffect(() => {
    const timer = setTimeout(() => {
      setShowIntro(false)
    }, 6500) // intro animation length

    return () => clearTimeout(timer)
  }, [])

  if(showIntro){
    return <IntroAnimation />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
