import React from 'react';

const Speedometer = ({ value, speed, unit = "KM/H", size = 180, decimals = 0 }) => {
    const displayValue = value !== undefined ? value : speed;
    return (
        <div className="flex flex-col items-center justify-center relative z-10" style={{ width: size }}>
            <div className="text-6xl font-black text-white tracking-tighter drop-shadow-2xl text-center leading-none">
                {typeof displayValue === 'number' ? displayValue.toFixed(decimals) : (displayValue || 0)}
            </div>
            <div className="text-xl font-medium text-gray-400 mt-[-5px] whitespace-nowrap">{unit}</div>
        </div>
    );
};

export default Speedometer;
