import { BrowserRouter, Routes, Route } from "react-router-dom"
import { useState, useEffect } from "react"

import './App.css'

import { IntroAnimation } from "./components/IntroAnimation"
import Home from "./pages/Home"

function App() {
  const [showIntro, setShowIntro] = useState(true)

  // Initialize theme from localStorage or prefers-color-scheme
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    let theme;
    if (savedTheme) {
      theme = savedTheme;
    } 
    else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      theme = "dark"
    }
    else {
      theme = "light";
    }
    
    // Apply theme to document root
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    
    localStorage.setItem("theme", theme);
    console.log(localStorage.getItem("theme"))
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowIntro(false)
    }, 10000) // intro animation length

    return () => clearTimeout(timer)
  }, [])

  if(showIntro){
    return (
      <div className = "animationContainer">
        <IntroAnimation />
      </div>
  )}

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
