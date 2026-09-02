'use client';

export default function HackerWatermark() {
  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      zIndex: -3,
      opacity: 0.3,
      pointerEvents: 'none',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <svg 
        width="700" 
        height="700" 
        viewBox="0 0 400 400" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        style={{
          filter: 'drop-shadow(0 0 50px rgba(0, 255, 136, 0.5))'
        }}
      >
        {/* Hacker skull icon */}
        <path 
          d="M200 50C140 50 90 100 90 160V200C90 240 110 280 140 300V340C140 350 150 360 160 360H240C250 360 260 350 260 340V300C290 280 310 240 310 200V160C310 100 260 50 200 50Z" 
          fill="#00ff88"
          opacity="1"
        />
        
        {/* Eyes */}
        <circle cx="160" cy="160" r="25" fill="#05080a" />
        <circle cx="240" cy="160" r="25" fill="#05080a" />
        
        {/* Glowing pupils */}
        <circle cx="160" cy="160" r="12" fill="#00ff88">
          <animate attributeName="opacity" values="0.5;1;0.5" duration="2s" repeatCount="indefinite" />
        </circle>
        <circle cx="240" cy="160" r="12" fill="#00ff88">
          <animate attributeName="opacity" values="0.5;1;0.5" duration="2s" repeatCount="indefinite" />
        </circle>
        
        {/* Nose */}
        <path d="M200 180L185 230H215L200 180Z" fill="#05080a" />
        
        {/* Teeth */}
        <rect x="165" y="240" width="18" height="25" fill="#05080a" />
        <rect x="191" y="240" width="18" height="25" fill="#05080a" />
        <rect x="217" y="240" width="18" height="25" fill="#05080a" />
        
        {/* Circuit lines */}
        <path 
          d="M90 160H60M310 160H340M200 50V20" 
          stroke="#00ff88" 
          strokeWidth="4"
          opacity="0.8"
        />
        
        {/* Binary code decoration */}
        <text 
          x="40" 
          y="380" 
          fill="#00ff88" 
          fontSize="14" 
          fontFamily="monospace"
          opacity="0.8"
          fontWeight="bold"
        >
          01001000 01000001 01000011 01001011 01000101 01010010
        </text>
        
        <text 
          x="200" 
          y="395" 
          fill="#00ff88" 
          fontSize="16" 
          fontFamily="monospace"
          opacity="0.9"
          textAnchor="middle"
          fontWeight="bold"
        >
          SYSTEM SECURE
        </text>
        
        {/* Circuit patterns */}
        <circle cx="60" cy="160" r="8" fill="#00ff88" opacity="0.9">
          <animate attributeName="r" values="6;10;6" duration="1.5s" repeatCount="indefinite" />
        </circle>
        <circle cx="340" cy="160" r="8" fill="#00ff88" opacity="0.9">
          <animate attributeName="r" values="6;10;6" duration="1.5s" repeatCount="indefinite" />
        </circle>
        <circle cx="200" cy="20" r="8" fill="#00ff88" opacity="0.9">
          <animate attributeName="r" values="6;10;6" duration="1.5s" repeatCount="indefinite" />
        </circle>
      </svg>
    </div>
  );
}
