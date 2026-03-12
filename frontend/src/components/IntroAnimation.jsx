import { useEffect, useState } from "react"
import { motion } from "framer-motion"

import './introanimation.css'

function calculatePathData() {
  const points = [
    // I
    [288, 192], [288, 250],
    
    // N
    [308, 247.5], // Route to N's left stem
    [308, 196], // Draw left stem up
    [348, 250],     // Draw diagonal down to right stem
    [348, 192],     // Draw right stem up

    // K 
    [363, 193], // Route to K's stem
    [363, 247.5], // Draw stem down
    [364, 221],   // Retrace the stem back UP to the middle junction
    [395, 192],     // Draw upper arm outward
    [364, 221],   // Retrace upper arm back DOWN to the middle junction
    [395, 250],     // Draw lower arm outward

    // I 
    [458, 192], // Route to I top
    [458, 250], // Draw stem down

    // N
    [477, 247.5], // Route to N's stem
    [477, 189.5], // Draw stem up 
    [516, 250],     // Draw diagonal down to right stem
    [516, 192],     // Draw right stem up

    // Translates the toolhead directly to the second line.
    [303.5, 332.5],

    // --- THIRD WORD: 3DP ---

    // 3 
    [303.5, 335],   // Start at top left tip
    [327.5, 318], // Trace to top arc peak
    [348, 335],     // Trace to top right curve
    [327.5, 348.5], // Trace into the middle indent
    [348, 368],     // Trace to bottom right curve
    [327.5, 383.5], // Trace to bottom arc peak
    [303.5, 369.5], // Finish at bottom left tip

    // D 
    [377, 377.5], // Route to D stem bottom
    [377, 319.5], // Draw stem up
    [410, 336],   // Trace top curve
    [420, 350],     // Trace right outer arc 
    [405, 380],     // Trace bottom curve
    [369.5, 380],   // Close back to stem bottom

    // P 
    [450, 377.5], // Route to P stem bottom
    [450, 323], // Draw stem up
    [475, 323],   // Trace top curve
    [488, 338],     // Trace right outer arc
    [475, 354],     // Trace bottom curve
    [441.5, 354],    // Go to the stem's middle point

    [530,400]
  ];
// Length = distance between points
  // Time = how long it takes 
  let totalLength = 0;
  let totalTime = 0;
  const segmentLengths = [];
  const segmentTime = [];
  
  for (let i = 1; i < points.length; i++) {
    const dx = points[i][0] - points[i - 1][0];
    const dy = points[i][1] - points[i - 1][1];
    const dist = Math.sqrt(dx * dx + dy * dy);
    // calculating length using pythagorean
    
    segmentLengths.push(dist);
    totalLength += dist;
    
    let time = dist;
    
    // if the point is coords 19, which is the jump from top to bottom line
    if (i === 19) {
      time *= 0.000000002;
    }
    
    segmentTime.push(time);
    totalTime += time;
  }

  // Generate normalized timings for travelling between coords
  const times = [0];
  const pathLengths = [0];
  let currentLength = 0;
  let currentTime = 0;
  
  for (let i = 0; i < segmentLengths.length; i++) {
    currentLength += segmentLengths[i];
    pathLengths.push(currentLength / totalLength);
    
    currentTime += segmentTime[i];
    times.push(currentTime / totalTime);
  }

  // Extract separate arrays for X and Y coordinates to feed into the toolhead animation
  const xKeyframes = points.map(p => p[0]);
  const yKeyframes = points.map(p => p[1]);
  
  // Create an SVG path string ('M x y L x y L x y...') for the mask stroke
  const pathD = `M ${points[0][0]} ${points[0][1]} ` + points.slice(1).map(p => `L ${p[0]} ${p[1]}`).join(' ');

  return { xKeyframes, yKeyframes, pathLengths, times, pathD };
}

// Compute values once on mount
const { xKeyframes, yKeyframes, pathLengths, times, pathD } = calculatePathData();

const AnimatedLine = ({ x1, y1, x2, y2, stroke, strokeWidth, dir, isVisible }) => {
  // Determine off-screen starting coordinates based on direction
  const hiddenX = dir === 'left' ? -800 : dir === 'right' ? 800 : 0;
  const hiddenY = dir === 'top' ? -800 : dir === 'bottom' ? 800 : 0;
  
  return (
    <motion.line 
      x1={x1} y1={y1} x2={x2} y2={y2} 
      stroke={stroke} strokeWidth={strokeWidth}
      initial={{ x: hiddenX, y: hiddenY, opacity: 0 }}
      animate={{ 
        x: isVisible ? 0 : hiddenX, 
        y: isVisible ? 0 : hiddenY, 
        opacity: isVisible ? 1 : 0 
      }}
      transition={{ duration: 0.7, ease: "easeInOut" }}
    />
  );
};

// function for circles to fly in and appear 
const AnimatedCircle = ({ cx, cy, r, fill, stroke, strokeWidth, dir, isVisible }) => {
  const hiddenX = dir === 'left' ? -800 : dir === 'right' ? 800 : 0;
  const hiddenY = dir === 'top' ? -800 : dir === 'bottom' ? 800 : 0;
  
  return (
    <motion.circle 
      cx={cx} cy={cy} r={r} fill={fill} stroke={stroke} strokeWidth={strokeWidth}
      initial={{ x: hiddenX, y: hiddenY, opacity: 0 }}
      animate={{ 
        x: isVisible ? 0 : hiddenX, 
        y: isVisible ? 0 : hiddenY, 
        opacity: isVisible ? 1 : 0 
      }}
      transition={{ duration: 0.7, ease: "easeInOut" }}
    />
  );
};

export function IntroAnimation({ fadeOut }){
  const [phase, setPhase] = useState("hidden")

  useEffect(()=> {
    let isCancelled = false;
    function delay(ms){
      return new Promise(resolve => setTimeout(resolve, ms))
    }
    
    async function runLoop(){
      setPhase("assembling")
      await delay(600)
      setPhase("paperIn")
      await delay(500)
      setPhase("assembled")
      await delay(400)
      setPhase("writing")
      await delay(6500)
      setPhase("paperOut")
      await delay(800)
      setPhase("disassembling")
      await delay(1000)
      setPhase("hidden")
      await delay(500)
    }

    async function loopForever(){
      while (!isCancelled){
        await runLoop();
      }
    }

    loopForever();

    return () => { isCancelled = true };
  }, []);

  // Determine if the physical components of the printer should be visible on screen
  const isVisible = phase === 'assembling' || phase === 'assembled' || phase === 'paperIn' || phase === 'writing' || phase === 'paperOut';
  const paperEntered = phase === 'paperIn' || phase === 'assembled' || phase === 'writing' || phase === 'paperOut';
  const paperExiting = phase === 'paperOut';

  return (
    <div className={`animation ${fadeOut ? 'fade-out' : ''}`}>
      <svg viewBox="-200 -162 1200 918" preserveAspectRatio="xMidYMid meet">
        <defs>
          {/* 
            The mask determines what parts of the text are visible. 
            It starts empty (pathLength = 0) and smoothly "grows" (pathLength = 1) exactly as the toolhead moves.
          */}
          <mask id="write-mask">
            <motion.path
              d={pathD}
              fill="none"
              stroke="white"
              strokeWidth="16" // change this if mask is too large
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ 
                pathLength: phase === 'writing' ? pathLengths : phase === 'paperOut' || phase === 'disassembling' ? 1 : 0,
                opacity: phase === 'writing' || phase === 'paperOut' || phase === 'disassembling' ? 1 : 0
              }}
              transition={{ 
                // Time matches the toolhead exactly, using the calculated custom `times` array for speed-ups
                pathLength: { duration: phase === 'writing' ? 6 : 0, times: phase === 'writing' ? times : undefined, ease: "linear" },
                opacity: { duration: 0 }
              }}
            />
          </mask>
        </defs>

        {/*Printer Edges*/}
        <AnimatedLine x1="200" y1="150" x2="600" y2="150" stroke="var(--svg-color)" strokeWidth="4" dir="right" isVisible={isVisible} />
        <AnimatedLine x1="600" y1="150" x2="600" y2="450" stroke="var(--svg-color)" strokeWidth="4" dir="bottom" isVisible={isVisible} />
        <AnimatedLine x1="600" y1="450" x2="200" y2="450" stroke="var(--svg-color)" strokeWidth="4" dir="left" isVisible={isVisible} />
        <AnimatedLine x1="200" y1="450" x2="200" y2="150" stroke="var(--svg-color)" strokeWidth="4" dir="top" isVisible={isVisible} />

        <motion.rect
          x="230"
          y="170"
          width="340"
          height="260"
          stroke="var(--svg-color)"
          strokeWidth="2"
          fill="var(--bg-color)"
          initial={{ y: 800, opacity: 0 }}
          animate={{
            y: paperExiting ? 800 : paperEntered ? 0 : 800,
            opacity: paperExiting ? 0 : paperEntered ? 1 : 0
          }}
          transition={{ duration: 0.7, ease: "easeInOut" }}
        />

        {/* Masked Text Group: Anything inside this group is hidden unless covered by the growing mask above */}
        <motion.g
          initial={{ opacity: 0, y: 0 }}
          animate={{ 
            opacity: paperExiting ? 0 : isVisible ? 1 : 0,
            y: paperExiting ? 630 : 0
          }}
          transition={{ 
            opacity: { duration: 0.7 },
            y: { duration: 0.7, ease: "easeInOut" }
          }}
          mask="url(#write-mask)"
          fontFamily="'Red Hat Display', sans-serif" 
          fontSize="80" 
          fontWeight="500" 
          textAnchor="middle" 
          fill="var(--text-color)"
        >
          <text x="288" y="250">I</text>
          <text x="328" y="250">N</text>
          <text x="378" y="250">K</text>

          <text x="458" y="250">I</text>
          <text x="498" y="250">N</text>

          <text x="330" y="380">3</text>
          <text x="400" y="380">D</text>
          <text x="470" y="380">P</text>
        </motion.g>

        {/* 
          Toolhead Group 
          This moves as a single unified object across the screen along X/Y coordinates that exactly match the mask path.
        */}
        <motion.g
          initial={{ x: xKeyframes[0], y: yKeyframes[0] }}
          animate={{
            x: phase === 'writing' ? xKeyframes : phase === 'paperIn' || phase === 'assembled' || phase === 'assembling' ? xKeyframes[0] : xKeyframes[xKeyframes.length - 1],
            y: phase === 'writing' ? yKeyframes : phase === 'paperIn' || phase === 'assembled' || phase === 'assembling' ? yKeyframes[0] : yKeyframes[yKeyframes.length - 1],
          }}
          transition={{
            x: phase === 'writing' ? { duration: 6, times, ease: "linear" } : { duration: 0 },
            y: phase === 'writing' ? { duration: 6, times, ease: "linear" } : { duration: 0 },
          }}
        >
          {/* Toolhead Main Box */}
          <AnimatedLine x1="-30" y1="-48" x2="30" y2="-48" stroke="var(--svg-color)" strokeWidth="3" dir="left" isVisible={isVisible} />
          <AnimatedLine x1="30" y1="-48" x2="30" y2="-8" stroke="var(--svg-color)" strokeWidth="3" dir="top" isVisible={isVisible} />
          <AnimatedLine x1="30" y1="-8" x2="-30" y2="-8" stroke="var(--svg-color)" strokeWidth="3" dir="right" isVisible={isVisible} />
          <AnimatedLine x1="-30" y1="-8" x2="-30" y2="-48" stroke="var(--svg-color)" strokeWidth="3" dir="bottom" isVisible={isVisible} />
          
          {/* Marker Tip (Anchored directly at [0,0] so it aligns perfectly with the current X,Y keyframe coordinate) */}
          <AnimatedCircle cx="0" cy="0" r="8" fill="var(--bg-color)" stroke="var(--svg-color)" strokeWidth="3" dir="top" isVisible={isVisible} />
        </motion.g>
      </svg>
    </div>
  );
}
