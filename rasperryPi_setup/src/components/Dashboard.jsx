import React, { useState, useEffect } from 'react';
import { Settings, AlignJustify, Activity, Home, Wind, Crosshair, Heart, Thermometer } from 'lucide-react';
import Header from './Header';
import LinearBar from './LinearBar';
import StatusGauge from './StatusGauge';
import LineGraph from './LineGraph';
import Speedometer from './Speedometer';
import useBMSData from '../hooks/useBMSData';

const Dashboard = () => {
    // Connect to BMS backend - adjust URL for Raspberry Pi
    const bmsData = useBMSData('http://localhost:5000');

    const [speed, setSpeed] = useState(0);
    const [speedHistory, setSpeedHistory] = useState(new Array(20).fill(0));
    const [throttleHistory, setThrottleHistory] = useState(new Array(20).fill(0));

    // Estimated DTE Logic
    const [dteIndex, setDteIndex] = useState(0);
    const dteOffsets = [1, -2, 1, 2];

    useEffect(() => {
        const interval = setInterval(() => {
            setDteIndex(prev => (prev + 1) % dteOffsets.length);
        }, 20000); // Change every 20s
        return () => clearInterval(interval);
    }, []);

    // USER SIMULATION HELPERS (For when not connected)
    const THROTTLE_POINTS = [
        { x: 0, y: 0.0 },
        { x: 1, y: 2.0 },
        { x: 2, y: 1.9 },
        { x: 3, y: 2.5 },
        { x: 4, y: 4.0 },
        { x: 5, y: 4.4 }
    ];

    const getThrottleValue = (currentX) => {
        for (let i = 0; i < THROTTLE_POINTS.length - 1; i++) {
            const p1 = THROTTLE_POINTS[i];
            const p2 = THROTTLE_POINTS[i + 1];
            if (currentX >= p1.x && currentX <= p2.x) {
                const ratio = (currentX - p1.x) / (p2.x - p1.x);
                return p1.y + (p2.y - p1.y) * ratio;
            }
        }
        return currentX >= 5 ? 4.4 : 0;
    };

    // Use real data from bmsData if connected
    useEffect(() => {
        if (bmsData.esp32_connected || bmsData.connected) {
            const currentSpeed = bmsData.speed_kmph || 0;
            setSpeed(currentSpeed);
            setSpeedHistory(prev => [...prev.slice(1), currentSpeed]);

            const currentThrottle = bmsData.throttle || 0;
            setThrottleHistory(prev => [...prev.slice(1), currentThrottle]);
        }
    }, [bmsData.speed_kmph, bmsData.throttle, bmsData.esp32_connected, bmsData.connected]);

    // Simulation Loop (runs only if NOT connected)
    useEffect(() => {
        const startTime = Date.now();
        const interval = setInterval(() => {
            const now = Date.now();
            const totalElapsed = now - startTime;

            if (!bmsData.esp32_connected && !bmsData.connected) {
                // Simulate Speed
                const speedPeriod = 3000;
                const speedPhase = (totalElapsed % speedPeriod) / speedPeriod;
                const simSpeed = 80 * Math.sin(speedPhase * Math.PI);
                setSpeed(simSpeed);
                setSpeedHistory(prev => [...prev.slice(1), simSpeed]);

                // Simulate Throttle
                const throttlePeriod = 4000;
                const cycleElapsed = totalElapsed % throttlePeriod;
                const progress = cycleElapsed / throttlePeriod;
                const pingPongX = (progress < 0.5 ? progress * 2 : 2 - progress * 2) * 5;
                const simThrottle = getThrottleValue(pingPongX);
                setThrottleHistory(prev => [...prev.slice(1), simThrottle]);
            }
        }, 100);
        return () => clearInterval(interval);
    }, [bmsData.esp32_connected, bmsData.connected]);

    return (
        <div className="w-[1024px] h-[600px] bg-[#050505] p-3 flex flex-col gap-2 text-gray-200 font-sans selection:bg-neon-cyan selection:text-black overflow-hidden">
            <Header piBattery={bmsData.pi_battery} />

            {/* Main Grid Layout - Asymmetric Split */}
            <div className="flex-1 grid grid-cols-12 gap-0 pb-1">

                {/* LEFT MAIN PANEL (Span 9) */}
                <div className="col-span-9 flex flex-col gap-2 pr-6 border-r border-white/10 overflow-hidden">

                    {/* Top Row: Title, Cards, Gauges */}
                    <div className="flex items-end justify-between px-2 mb-2 relative z-20">
                        <div className="flex flex-col items-start gap-2">
                            <h1 className="text-3xl font-black italic tracking-wider text-white">E-BIKE DATA</h1>

                            {/* Cards Row: Voltage/Current + Power */}
                            <div className="flex items-center gap-3 w-[26rem]">
                                <div className="glass-panel bg-black/40 backdrop-blur-xl rounded-2xl p-4 border border-white/10 shadow-2xl flex-1 h-[7rem] flex flex-col justify-center">
                                    <LinearBar
                                        variant="dual-split"
                                        leftColor="bg-[#00f2ff]"
                                        rightColor="bg-neon-orange"
                                        leftLabel={`${bmsData.voltage.toFixed(1)} V`}
                                        rightLabel={`${bmsData.current.toFixed(1)} A`}
                                        leftValue={bmsData.voltage}
                                        leftMax={80}
                                        rightValue={bmsData.current}
                                        rightMax={5}
                                    />
                                </div>

                                <div className="glass-panel bg-black/40 backdrop-blur-xl rounded-2xl p-4 border border-white/10 shadow-2xl flex-1 h-[7rem] flex flex-col justify-end">
                                    <div className="flex flex-col items-start mb-2 px-1">
                                        <span className="text-[10px] text-gray-400 font-bold tracking-widest uppercase">POWER</span>
                                        <span className="text-lg font-black italic text-white tracking-wide">
                                            {(bmsData.power / 1000).toFixed(2)} KW
                                        </span>
                                    </div>
                                    <LinearBar
                                        allowGradient={true}
                                        scaleLabels={['0.0', '0.1', '0.2', '0.3']}
                                        numericValue={bmsData.power / 1000}
                                        max={0.3}
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="glass-panel rounded-[1.8rem] px-8 py-6 flex items-center gap-6 bg-black/20 border border-white/10 shadow-lg">
                            <StatusGauge
                                value={bmsData.soc}
                                label="SOC"
                                size={140}
                                strokeWidth={12}
                                rotation={90}
                                segments={[
                                    { percent: 50, color: '#00f2ff' },
                                    { percent: 25, color: '#00ff9d' }
                                ]}
                            />
                            <StatusGauge value={bmsData.soh} size={110} strokeWidth={10} label="SOH" color="#00ff9d" rotation={180} />
                        </div>
                    </div>

                    {/* MAIN DISPLAY AREA (Dual Graph Split) */}
                    <div className="flex-1 grid grid-cols-2 gap-4 pb-2">

                        {/* LEFT: MOTOR SPEED GRAPH */}
                        <div className="flex flex-col relative border border-white/40 rounded-bl-[2rem] overflow-hidden bg-black/20">
                            <div className="text-white font-bold tracking-[0.3em] text-xs mb-2 z-10 w-full text-center mt-2 font-montserrat">
                                MOTOR SPEED (KM/H)
                            </div>
                            <div className="flex-1 relative">
                                <LineGraph
                                    data={speedHistory}
                                    color="#00f2ff"
                                    maxVal={120}
                                    yLabels={['120', '90', '60', '30']}
                                    xLabels={['0', '2', '4', '6', '8', '10']}
                                />
                                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-30">
                                    <Speedometer speed={Math.round(speed)} size={180} />
                                </div>
                            </div>
                        </div>

                        {/* RIGHT: THROTTLE POSITION GRAPH (Now optimized for % data) */}
                        <div className="flex flex-col relative border border-white/40 rounded-br-[2rem] overflow-hidden bg-black/20">
                            <div className="text-white font-bold tracking-[0.3em] text-[10px] mb-2 z-10 w-full text-center mt-2 font-montserrat">
                                THROTTLE POSITION (%)
                            </div>
                            <div className="flex-1 relative">
                                <LineGraph
                                    data={throttleHistory}
                                    color="#ff5e00"
                                    maxVal={100}
                                    yLabels={['100', '75', '50', '25', '0']}
                                    xLabels={['0', '2', '4', '6', '8', '10']}
                                />
                                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-30">
                                    <Speedometer value={throttleHistory[throttleHistory.length - 1]} unit="%" decimals={0} size={180} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT SIDEBAR PANEL (Span 3) */}
                <div className="col-span-3 flex flex-col relative h-full pl-6">
                    <div className="absolute inset-0 bg-[#0f0f0f] rounded-[2.5rem] -z-10 border border-white/5"></div>
                    <div className="flex flex-col h-full p-5 gap-4">
                        <div className="w-full bg-[#141414] border border-white/5 rounded-2xl p-4 flex justify-between items-center">
                            <div className="bg-[#1a1a1a] rounded-full px-4 py-2 flex items-center gap-4 border border-white/5">
                                <Settings size={20} className="text-gray-400" />
                                <Heart size={20} className="text-white fill-white" />
                                <AlignJustify size={20} className="text-gray-400 rotate-90" />
                            </div>
                            <div className="w-10 h-10 rounded-full bg-[#1a1a1a] border border-white/5 flex items-center justify-center relative">
                                <div className="grid grid-cols-2 gap-[2px]">
                                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                                    <div className="w-1 h-1 bg-neon-orange rounded-full"></div>
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 bg-[#141414] rounded-3xl border border-white/40 flex flex-col relative overflow-hidden">
                            <div className="flex-1 flex flex-col items-center justify-center p-4 border-b border-white/5 w-full">
                                <div className="text-[10px] text-white font-bold tracking-widest uppercase mb-3 text-center w-full font-montserrat">TEMPERATURE</div>
                                <div className="flex flex-col gap-2 w-full px-2">
                                    {[0, 1, 2].map((idx) => (
                                        <div key={idx} className="flex items-center justify-between bg-white/5 rounded-lg p-2 px-3 border border-[#ff5e00]/40">
                                            <div className="flex items-center gap-2 text-[#00f2ff]">
                                                <Thermometer size={14} />
                                                <span className="text-[10px] font-bold tracking-wider">T{idx + 1}</span>
                                            </div>
                                            <div className="flex items-baseline gap-1">
                                                <span className="text-lg font-black italic text-white">
                                                    {bmsData.temperatures ? bmsData.temperatures[idx] : 0}
                                                </span>
                                                <span className="text-[10px] text-gray-400 font-bold">°C</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="flex-1 flex flex-col justify-center items-center p-2 bg-[#141414]/50 border-b border-white/5 relative group">
                                <span className="text-[10px] text-gray-500 font-bold tracking-widest uppercase mb-1">DRIVE MODE</span>
                                <div className="flex flex-col items-center">
                                    <span className={`text-2xl font-black italic tracking-wider ${bmsData.speed_mode === 'POWER' ? 'text-red-500' :
                                        bmsData.speed_mode === 'SPORTS' ? 'text-neon-orange' :
                                            'text-neon-cyan'
                                        }`}>
                                        {bmsData.speed_mode || 'ECONOMY'}
                                    </span>
                                    <div className="flex gap-1 mt-1">
                                        {[0, 1, 2].map((m) => (
                                            <div key={m} className={`w-3 h-1 rounded-full ${(bmsData.speed_mode === 'POWER' && m === 0) ||
                                                (bmsData.speed_mode === 'ECONOMY' && m === 1) ||
                                                (bmsData.speed_mode === 'SPORTS' && m === 2)
                                                ? 'bg-white' : 'bg-white/10'
                                                }`}></div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="flex-1 flex flex-col justify-center items-center p-2 bg-[#141414]/50 relative group">
                                <span className="text-[10px] text-gray-500 font-bold tracking-widest uppercase mb-1">EST. DISTANCE</span>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-3xl font-black italic text-white tracking-wider">
                                        {Math.round(bmsData.soc + (dteOffsets[dteIndex] || 0))}
                                    </span>
                                    <span className="text-xs font-bold text-neon-orange">KM</span>
                                </div>
                                <div className="text-[8px] text-gray-600 mt-1">To Empty</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
