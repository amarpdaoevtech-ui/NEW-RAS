import React from 'react';

const ANIM = `
  @keyframes t7-active-ring {
    0%,100%{ transform:scale(1); opacity:0.6; }
    50%    { transform:scale(1.4); opacity:0; }
  }
  @keyframes t7-active-dot {
    0%,100%{ box-shadow:0 0 8px var(--sc),0 0 18px var(--sc60); }
    50%    { box-shadow:0 0 16px var(--sc),0 0 36px var(--sc60),0 0 60px var(--sc30); }
  }
  @keyframes t7-row-bg {
    0%,100%{ opacity:0.06; }
    50%    { opacity:0.12; }
  }
  @keyframes t7-corner-glow {
    0%,100%{ opacity:0.25; }
    50%    { opacity:0.55; }
  }
`;

const STATE_DEFS = [
  { id:1, color:'#64748B', label:'PARK'    },
  { id:2, color:'#F59E0B', label:'REVERSE' },
  { id:3, color:'#38BDF8', label:'NEUTRAL' },
  { id:4, color:'#00e87a', label:'DRIVE'   },
];

export default function TileType7({
  label         = 'GEAR STATE',
  state         = 4,
  state_1_label = 'PARK',    state_2_label = 'REVERSE',
  state_3_label = 'NEUTRAL', state_4_label = 'DRIVE',
  state_1_color = '#64748B', state_2_color = '#F59E0B',
  state_3_color = '#38BDF8', state_4_color = '#00e87a',
}) {
  const stateList = [
    { id:1, label:state_1_label, color:state_1_color },
    { id:2, label:state_2_label, color:state_2_color },
    { id:3, label:state_3_label, color:state_3_color },
    { id:4, label:state_4_label, color:state_4_color },
  ].filter(s=>s.label);

  const active = stateList.find(s=>s.id===state) || stateList[stateList.length-1];

  return (
    <div style={{
      width:'100%', height:'100%',
      background:'linear-gradient(145deg,#0a1e2e 0%,#060c14 100%)',
      border:`1px solid ${active.color}35`,
      borderRadius:12,
      padding:'10px 12px',
      boxSizing:'border-box',
      display:'flex', flexDirection:'column',
      fontFamily:"'Inter',sans-serif",
      color:'#F1F5F9',
      position:'relative', overflow:'hidden',
    }}>
      <style>{ANIM}</style>

      {/* big corner ambient glow */}
      <div style={{
        position:'absolute', bottom:-30, right:-30,
        width:110, height:110,
        background:`radial-gradient(circle,${active.color}35 0%,${active.color}10 45%,transparent 70%)`,
        animation:'t7-corner-glow 2.5s ease-in-out infinite',
        pointerEvents:'none',
      }}/>
      <div style={{
        position:'absolute', top:-20, left:-20,
        width:70, height:70,
        background:`radial-gradient(circle,${active.color}20 0%,transparent 70%)`,
        pointerEvents:'none',
      }}/>

      {/* LABEL */}
      <div style={{
        fontSize:8, fontWeight:700, letterSpacing:'0.14em',
        textTransform:'uppercase', marginBottom:6,
        background:`linear-gradient(90deg,${active.color},#ffffffaa)`,
        WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent',
        borderBottom:`1px solid ${active.color}20`,
        paddingBottom:5,
      }}>{label.slice(0,14)}</div>

      {/* STATE ROWS */}
      <div style={{ flex:1, display:'flex', flexDirection:'column', gap:3, justifyContent:'center' }}>
        {stateList.map(s=>{
          const isActive = s.id === state;
          const sc60    = s.color+'99';
          const sc30    = s.color+'4D';

          return (
            <div key={s.id} style={{
              display:'flex', alignItems:'center', gap:8,
              padding:'4px 6px',
              borderRadius:6,
              background: isActive ? `${s.color}12` : 'transparent',
              border: isActive ? `1px solid ${s.color}30` : '1px solid transparent',
              opacity: isActive ? 1 : 0.25,
              transition:'all 0.35s ease-out',
              position:'relative', overflow:'hidden',
              animation: isActive ? 't7-row-bg 2s ease-in-out infinite' : 'none',
            }}>
              {/* indicator dot with pulse ring */}
              <div style={{ position:'relative', width:14, height:14, flexShrink:0 }}>
                {/* pulse ring */}
                {isActive && (
                  <div style={{
                    position:'absolute', inset:-4,
                    borderRadius:'50%',
                    border:`1.5px solid ${s.color}`,
                    animation:'t7-active-ring 1.8s ease-out infinite',
                  }}/>
                )}
                {/* solid dot */}
                <div style={{
                  width:14, height:14, borderRadius:'50%',
                  background: isActive ? s.color : '#1E3A5F',
                  '--sc':s.color,'--sc60':sc60,'--sc30':sc30,
                  animation: isActive ? 't7-active-dot 2s ease-in-out infinite' : 'none',
                  transition:'all .3s ease-out',
                  display:'flex', alignItems:'center', justifyContent:'center',
                }}>
                  {isActive && (
                    <div style={{ width:5,height:5,borderRadius:'50%',background:'rgba(255,255,255,0.9)' }}/>
                  )}
                </div>
              </div>

              {/* state name */}
              <span style={{
                flex:1,
                fontSize: isActive ? 13 : 9,
                fontWeight: isActive ? 900 : 600,
                fontFamily:"'Orbitron',sans-serif",
                color: isActive ? '#F1F5F9' : '#334155',
                letterSpacing:'0.04em',
                textShadow: isActive ? `0 0 10px ${s.color}70` : 'none',
                transition:'all .3s ease-out',
              }}>{s.label.toUpperCase().slice(0,9)}</span>

              {/* ON badge */}
              {isActive && (
                <div style={{
                  fontSize:7, fontWeight:800,
                  color:s.color,
                  background:`${s.color}18`,
                  border:`1px solid ${s.color}50`,
                  borderRadius:4,
                  padding:'1px 5px',
                  letterSpacing:'0.1em',
                  fontFamily:"'Orbitron',sans-serif",
                }}>ON</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
