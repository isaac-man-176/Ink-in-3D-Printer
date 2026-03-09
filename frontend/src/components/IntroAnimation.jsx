import { useEffect, useState } from "react"
import { motion } from "framer-motion"

export function IntroAnimation(){
  const [phase, setPhase] = useState("hidden")

  useEffect(()=> {
    let isCancelled = false;
    function delay(ms){
      return new Promise(resolve => setTimeout(resolve, ms))
    }
    
    async function runLoop(){
      console.log("hi")
      await delay(1000)
      setPhase("printerForming")
      console.log("bye")
      await delay(1000)
      setPhase("printerFormend")
      await delay(1000)
      setPhase("drawingTitle")
      await delay(1000)
      setPhase("titleDrawn")
      await delay(1000)
      setPhase("printerLeaving")
      await delay(1000)
      setPhase("hidden")
    }

    async function loopForever(){
      while (!isCancelled){
        await runLoop();
      }
    }

    loopForever();

    return () => { isCancelled = true };
  }, []);

  return(
    <p>Current Phase: {phase}</p>
  )
}

export default IntroAnimation