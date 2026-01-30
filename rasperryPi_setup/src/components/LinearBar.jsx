import React from 'react';

const LinearBar = ({
    label, value, subLabel, subValue, variant = "standard",
    leftColor = "bg-neon-blue", rightColor = "bg-neon-orange",
    allowGradient = false, scaleLabels, leftLabel, rightLabel,
    // New props for dynamic values
    leftValue, rightValue, leftMax = 80, rightMax = 10,
    numericValue, max = 100
}) => {
    if (variant === "dual-split") {
        return (
            <div className="w-full flex flex-col gap-1">
                {/* Top Labels & Values */}
                <div className="flex justify-between items-end mb-1 px-1">
                    <div className="flex flex-col items-start">
                        <span className="text-[10px] text-gray-400 font-bold tracking-widest uppercase">VOLTAGE</span>
                        <span className="text-xl font-black italic text-white tracking-wide">{leftLabel || '0 V'}</span>
                    </div>
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] text-gray-400 font-bold tracking-widest uppercase">CURRENT</span>
                        <span className="text-xl font-black italic text-[#ff5e00] tracking-wide">{rightLabel || '0 A'}</span>
                    </div>
                </div>

                {/* Split Bar with Center Origin */}
                <div className="flex w-full h-2 bg-[#1a1a1a] rounded-full overflow-hidden relative">
                    {/* Left Side (Voltage) - Fills Right to Left */}
                    <div className="w-1/2 h-full flex justify-end bg-[#262626] border-r border-black/50">
                        <div
                            className={`${leftColor} h-full rounded-l-full transition-all duration-300 ease-out`}
                            style={{
                                width: leftValue !== undefined ? `${Math.min((leftValue / leftMax) * 100, 100)}%` : '80%'
                            }}
                        ></div>
                    </div>

                    {/* Right Side (Current) - Fills Left to Right */}
                    <div className="w-1/2 h-full flex justify-start bg-[#262626] border-l border-black/50">
                        <div
                            className={`${rightColor} h-full rounded-r-full transition-all duration-300 ease-out`}
                            style={{
                                width: rightValue !== undefined ? `${Math.min((rightValue / rightMax) * 100, 100)}%` : '60%'
                            }}
                        ></div>
                    </div>
                </div>

                {/* Scale for Split Variant */}
                <div className="flex justify-between text-[8px] font-bold text-gray-600 mt-1 px-0 font-mono tracking-wider">
                    <span>80</span>
                    <span>60</span>
                    <span>40</span>
                    <span>20</span>
                    <span className="text-white">0</span>
                    <span>1</span>
                    <span>2</span>
                    <span>3</span>
                    <span>4</span>
                    <span>5</span>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full flex flex-col gap-1.5">
            <div className="flex justify-between items-end">
                {label && <span className="text-[11px] text-gray-400 font-bold tracking-widest uppercase">{label}</span>}
                {value && <span className="text-2xl font-black italic text-white tracking-wide">{value}</span>}
            </div>

            <div className="w-full h-3 bg-[#1a1a1a] rounded-full overflow-hidden relative">
                <div
                    className={`h-full rounded-full relative ${allowGradient ? '' : leftColor} transition-all duration-300 ease-out`}
                    style={{
                        width: numericValue !== undefined ? `${Math.min((numericValue / max) * 100, 100)}%` : '75%',
                        background: allowGradient ? 'linear-gradient(90deg, #00f2ff 50%, #ff5e00 50%)' : undefined
                    }}
                >
                    {/* Shine effect */}
                    <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-white/20 skew-x-12"></div>
                </div>
            </div>

            {/* Optional Scale Labels */}
            {scaleLabels && (
                <div className="flex justify-between text-[8px] font-bold text-gray-600 mt-1 px-1 font-mono tracking-wider">
                    {scaleLabels.map((lbl, idx) => (
                        <span key={idx}>{lbl}</span>
                    ))}
                </div>
            )}

            {subLabel && !scaleLabels && (
                <div className="flex justify-end mt-1">
                    <span className="text-[10px] text-gray-500 font-bold tracking-wider">{subLabel}</span>
                </div>
            )}
        </div>
    );
};

export default LinearBar;
