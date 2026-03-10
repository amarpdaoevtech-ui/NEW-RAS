import React, { useState, useEffect } from 'react';
import { Settings, AlignJustify, Activity, Home, Wind, Crosshair, Heart, Thermometer } from 'lucide-react';
import Header from './Header';
import LinearBar from './LinearBar';
import StatusGauge from './StatusGauge';
import LineGraph from './LineGraph';
import Speedometer from './Speedometer';
import useBMSData from '../hooks/useBMSData';

const Dashboard = () => {
    // Connect to BMS backend - uses the same host as the frontend
    const bmsData = useBMSData(
        window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:5000'
            : `http://${window.location.hostname}:5000`
    );

    const [speed, setSpeed] = useState(0);
    const [speedHistory, setSpeedHistory] = useState(new Array(20).fill(0));
    const [throttleHistory, setThrottleHistory] = useState(new Array(20).fill(0));
    const [dte, setDte] = useState(0);
    const [dteAvgConsumption, setDteAvgConsumption] = useState(0);
    const [regenActive, setRegenActive] = useState(false);
    const [totalDistance, setTotalDistance] = useState(0);
    const [currentRideDistance, setCurrentRideDistance] = useState(0);

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

            // Update DTE from backend
            if (bmsData.dte !== undefined) {
                setDte(bmsData.dte);
            }
            if (bmsData.dte_avg_consumption !== undefined) {
                setDteAvgConsumption(bmsData.dte_avg_consumption);
            }
            if (bmsData.regen_active !== undefined) {
                setRegenActive(bmsData.regen_active);
            }
            if (bmsData.total_distance !== undefined) {
                setTotalDistance(bmsData.total_distance);
            }
            if (bmsData.current_ride_distance !== undefined) {
                setCurrentRideDistance(bmsData.current_ride_distance);
            }
        }
    }, [bmsData.speed_kmph, bmsData.throttle, bmsData.esp32_connected, bmsData.connected,
    bmsData.dte, bmsData.dte_avg_consumption, bmsData.regen_active,
    bmsData.total_distance, bmsData.current_ride_distance]);

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
                                        leftMax={84}
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
                    {/* Tighter sidebar to fit 7-inch 600px height */}
                    <div className="flex flex-col h-full p-3 gap-1">

                        {/* Icon bar — compact */}
                        <div className="w-full bg-[#141414] border border-white/5 rounded-xl p-2 flex justify-between items-center shrink-0">
                            <div className="bg-[#1a1a1a] rounded-full px-3 py-1 flex items-center gap-3 border border-white/5">
                                <Settings size={16} className="text-gray-400" />
                                <Heart size={16} className="text-white fill-white" />
                                <AlignJustify size={16} className="text-gray-400 rotate-90" />
                            </div>
                            <div className="w-8 h-8 rounded-full bg-[#1a1a1a] border border-white/5 flex items-center justify-center">
                                <div className="grid grid-cols-2 gap-[2px]">
                                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                                    <div className="w-1 h-1 bg-neon-orange rounded-full"></div>
                                </div>
                            </div>
                        </div>

                        {/* Main info card — takes remaining height */}
                        <div className="flex-1 bg-[#141414] rounded-3xl border border-white/40 flex flex-col relative overflow-hidden min-h-0">

                            {/* TEMPERATURE — compact */}
                            <div className="flex flex-col items-center p-2 border-b border-white/5 w-full shrink-0">
                                <div className="text-[9px] text-white font-bold tracking-widest uppercase mb-1 text-center w-full font-montserrat">TEMPERATURE</div>
                                <div className="flex flex-col gap-[3px] w-full px-1">
                                    {[0, 1, 2].map((idx) => (
                                        <div key={idx} className="flex items-center justify-between bg-white/5 rounded-md px-2 py-[2px] border border-[#ff5e00]/30">
                                            <div className="flex items-center gap-1 text-[#00f2ff]">
                                                <Thermometer size={11} />
                                                <span className="text-[9px] font-bold">T{idx + 1}</span>
                                            </div>
                                            <div className="flex items-baseline gap-[2px]">
                                                <span className="text-sm font-black italic text-white">
                                                    {bmsData.temperatures ? bmsData.temperatures[idx] : 0}
                                                </span>
                                                <span className="text-[8px] text-gray-400 font-bold">°C</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* EST. RANGE + Drive Mode badge + Distance rows */}
                            <div className="flex-1 flex flex-col justify-start items-center pt-4 px-3 pb-2 bg-[#141414]/50 min-h-0 overflow-hidden">

                                {/* Drive mode: compact inline badge */}
                                <div className="flex items-center gap-3 mb-3">
                                    <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">Mode:</span>
                                    <span className={`text-base font-black italic tracking-wider ${bmsData.speed_mode === 'POWER' ? 'text-red-400' :
                                        bmsData.speed_mode === 'SPORTS' ? 'text-neon-orange' :
                                            'text-neon-cyan'
                                        }`}>{bmsData.speed_mode || 'ECO'}</span>
                                </div>

                                {/* DTE big number */}
                                <span className="text-[10px] text-gray-400 font-bold tracking-widest uppercase">EST. RANGE</span>
                                <div className="flex items-baseline gap-2 mt-1">
                                    <span className="text-5xl font-black italic text-white tracking-wider leading-none">
                                        {dte > 0 ? Math.round(dte) : '--'}
                                    </span>
                                    <span className="text-lg font-bold text-neon-orange">KM</span>
                                </div>
                                <div className="text-[10px] text-gray-600 mb-4 font-bold uppercase tracking-tighter">To Empty</div>

                                {/* Distance rows */}
                                <div className="w-full border-t border-white/10 pt-4 flex flex-col gap-2">

                                    {/* Total ODO */}
                                    <div className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3 border border-[#00f2ff]/30 shadow-inner">
                                        <div className="flex flex-col leading-tight">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Total ODO</span>
                                            <span className="text-[9px] text-gray-600 font-bold">LIFETIME</span>
                                        </div>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-2xl font-black italic text-white">
                                                {totalDistance ? totalDistance.toFixed(1) : '0.0'}
                                            </span>
                                            <span className="text-xs text-[#00f2ff] font-bold">KM</span>
                                        </div>
                                    </div>

                                    {/* This Ride */}
                                    <div className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3 border border-neon-orange/30 shadow-inner">
                                        <div className="flex flex-col leading-tight">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">This Ride</span>
                                            <span className="text-[9px] text-gray-600 font-bold">SINCE BOOT</span>
                                        </div>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-2xl font-black italic text-white">
                                                {currentRideDistance ? currentRideDistance.toFixed(1) : '0.0'}
                                            </span>
                                            <span className="text-xs text-neon-orange font-bold">KM</span>
                                        </div>
                                    </div>

                                </div>

                                {/* Wh/km + regen */}
                                {dteAvgConsumption > 0 && (
                                    <div className="text-[10px] text-gray-400 mt-4 flex gap-2 items-center justify-center w-full font-bold">
                                        <span>{dteAvgConsumption.toFixed(1)} Wh/km</span>
                                        {regenActive && <span className="text-neon-cyan font-black animate-pulse">🔋 REGEN</span>}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
