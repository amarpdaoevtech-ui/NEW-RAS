import React from 'react';

const StatusGauge = ({ value, size = 100, strokeWidth = 8, color = "#00f2ff", trackColor = "#1a1a1a", label, showValue = true, rotation = -90, segments }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (value / 100) * circumference;

    return (
        <div className="flex flex-col items-center justify-center gap-2">
            <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
                {/* Background Ring (Track) */}
                <svg width={size} height={size} style={{ transform: `rotate(${rotation}deg)` }}>
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        stroke={trackColor}
                        strokeWidth={strokeWidth}
                        fill="transparent"
                        strokeLinecap="round"
                    />

                    {/* Render Segments if provided, else normal value circle */}
                    {segments ? (
                        segments.map((seg, i) => {
                            // Calculate previous total percentage to rotate/offset correctly
                            const prevPercents = segments.slice(0, i).reduce((acc, curr) => acc + curr.percent, 0);
                            const currentOffset = circumference - (seg.percent / 100) * circumference;
                            const rotateAngle = (prevPercents / 100) * 360;

                            return (
                                <circle
                                    key={i}
                                    cx={size / 2}
                                    cy={size / 2}
                                    r={radius}
                                    stroke={seg.color}
                                    strokeWidth={strokeWidth}
                                    fill="transparent"
                                    strokeDasharray={circumference}
                                    strokeDashoffset={currentOffset}
                                    strokeLinecap="round"
                                    style={{ transformOrigin: 'center', transform: `rotate(${rotateAngle}deg)` }}
                                />
                            );
                        })
                    ) : (
                        <circle
                            cx={size / 2}
                            cy={size / 2}
                            r={radius}
                            stroke={color}
                            strokeWidth={strokeWidth}
                            fill="transparent"
                            strokeDasharray={circumference}
                            strokeDashoffset={offset}
                            strokeLinecap="round"
                        />
                    )}

                </svg>
                {/* Value Text */}
                {showValue && (
                    <div className="absolute inset-0 flex items-center justify-center text-xl font-bold text-white">
                        {value}%
                    </div>
                )}
            </div>
            {label && <span className="text-[10px] text-gray-300 font-bold tracking-widest uppercase">{label}</span>}
        </div>
    );
};

export default StatusGauge;
