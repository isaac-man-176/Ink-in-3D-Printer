import { BrowserRouter, Routes, Route } from "react-router-dom"
import { useState, useEffect } from "react"

import './App.css'

import { IntroAnimation } from "./components/IntroAnimation"
import Home from "./pages/Home"

function App() {
  const [fadeOut, setFadeOut] = useState(false)

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    let theme;

    // First: checks to see if programmer inputs theme in overrideTheme
    let overrideTheme = ""
    if (overrideTheme != ""){
      theme = overrideTheme
    }

    // Second: checks if there is a locally saved theme (user ran program before)
    else if (savedTheme) {
      theme = savedTheme;
    } 

    // Third: checks system default
    else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      theme = "dark"
    }

    // Fallback: sets to light
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
      setFadeOut(true)
    }, 10000) // intro animation length

    return () => clearTimeout(timer)
  }, [])

  return (
    <>
        <BrowserRouter>
          <IntroAnimation fadeOut={fadeOut} />
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </BrowserRouter>
    </>
  );
}
export default App
