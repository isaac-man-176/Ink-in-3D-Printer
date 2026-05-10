import { useState } from "react"
import "./Home.css"

export default function Home() {
  const [mode, setMode] = useState(null)

  return (
    <div className="home-container">
      <div className="home-content">
        <h1 className="home-title">Ink in 3D Printer</h1>
        <p className="home-subtitle">Convert PDF documents into GCode</p>

        <div className="mode-selector">
          <div className="mode-card">
            <button 
              className={`mode-button ${mode === 'single' ? 'selected' : ''}`}
              onClick={() => setMode('single')}
            >
              Single Colour Mode
            </button>
            <p className="mode-description">
              Quick and easy to setup, requires less parts to be printed for the printer to plot the PDF
            </p>
          </div>

          <div className="mode-card">
            <button 
              className={`mode-button ${mode === 'multi' ? 'selected' : ''}`}
              onClick={() => setMode('multi')}
            >
              Multicolour Mode
            </button>
            <p className="mode-description">
              Requires more parts to be printed, but can switch between 6 markers or colours
            </p>
          </div>
        </div>

        {mode && (
          <button className="start-button">
            Start Conversion
          </button>
        )}
      </div>
    </div>
  )
}
