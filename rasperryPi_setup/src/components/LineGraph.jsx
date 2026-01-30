import React from 'react';

const LineGraph = ({
    data = [],
    color = "#00f2ff",
    maxVal = 120,
    maxX = 10,
    yLabels = ['120', '90', '60', '30'],
    xLabels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
}) => {
    // Generate path based on data
    // Supports two modes:
    // 1. Array of numbers: [y1, y2...] -> Distributed evenly across X
    // 2. Array of objects: [{x:0,y:0}, {x:5,y:50}] -> XY Plot based on maxX/maxVal

    const height = 150;
    const width = 1000;

    const getPoints = (arr) => {
        if (!arr || arr.length === 0) return `M 0,${height} L ${width},${height}`;

        // Check for XY mode
        const isXY = typeof arr[0] === 'object'; // Simple check

        if (isXY) {
            return arr.map((pt, i) => {
                const x = (pt.x / maxX) * width;
                const y = height - (pt.y / maxVal) * height;
                return `${i === 0 ? 'M' : 'L'} ${x},${y}`;
            }).join(' ');
        }

        // Standard Time-Series Mode
        const stepX = width / (Math.max(arr.length - 1, 1));

        return arr.map((val, i) => {
            const x = i * stepX;
            // Clamp value to maxVal to avoid drawing outside
            const safeVal = Math.min(Math.max(val, 0), maxVal);
            const y = height - (safeVal / maxVal) * height;
            return `${i === 0 ? 'M' : 'L'} ${x},${y}`;
        }).join(' ');
    };

    const pathData = getPoints(data);
    const areaPathData = `${pathData} V ${height} L 0,${height} Z`;

    return (
        <div className="w-full h-full absolute inset-0">
            <svg className="w-full h-full" preserveAspectRatio="none">
                <defs>
                    <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity="0.1" />
                        <stop offset="100%" stopColor={color} stopOpacity="0" />
                    </linearGradient>
                </defs>

                {/* Grid Lines aligned with Values */}
                <line x1="0" y1="25%" x2="100%" y2="25%" stroke="rgba(255,255,255,0.08)" />
                <line x1="0" y1="50%" x2="100%" y2="50%" stroke="rgba(255,255,255,0.08)" />
                <line x1="0" y1="75%" x2="100%" y2="75%" stroke="rgba(255,255,255,0.08)" />
            </svg>

            {/* Main Graph SVG */}
            <svg viewBox="-10 0 1010 150" className="w-full h-full absolute inset-0 -ml-1" preserveAspectRatio="none">
                <defs>
                    <linearGradient id={`gradient-fill-${color}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity="0.2" />
                        <stop offset="100%" stopColor={color} stopOpacity="0" />
                    </linearGradient>
                </defs>

                {/* Y-Axis Line & Ticks */}
                <line x1="0" y1="0" x2="0" y2="150" stroke="rgba(255,255,255,0.2)" strokeWidth="2" vectorEffect="non-scaling-stroke" />

                {/* Ticks matching values */}
                <line x1="0" y1="37.5" x2="10" y2="37.5" stroke="rgba(255,255,255,0.2)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                <line x1="0" y1="75" x2="10" y2="75" stroke="rgba(255,255,255,0.2)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                <line x1="0" y1="112.5" x2="10" y2="112.5" stroke="rgba(255,255,255,0.2)" strokeWidth="2" vectorEffect="non-scaling-stroke" />

                <path
                    d={pathData}
                    fill="none"
                    stroke={color}
                    strokeWidth="4"
                    vectorEffect="non-scaling-stroke"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
                <path
                    d={areaPathData}
                    fill={`url(#gradient-fill-${color})`}
                    stroke="none"
                />
            </svg>

            {/* Y-Axis Labels inside */}
            <div className="absolute left-2 top-0 bottom-4 flex flex-col justify-between py-6 text-[10px] text-gray-500 font-mono font-bold pointer-events-none">
                {yLabels.map((label, i) => (
                    <span key={i}>{label}</span>
                ))}
            </div>

            {/* X-Axis Labels */}
            <div className="absolute left-6 right-6 bottom-1 flex justify-between px-0 text-[10px] text-gray-500 font-mono font-bold pointer-events-none">
                {xLabels.map((label, i) => (
                    <span key={i}>{label}</span>
                ))}
            </div>
        </div>
    );
};

export default LineGraph;
