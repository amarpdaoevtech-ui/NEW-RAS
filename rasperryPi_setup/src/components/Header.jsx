import React from 'react';
import { Wifi, Battery } from 'lucide-react';

const Header = ({ piBattery }) => {
    return (
        <div className="flex justify-end items-center w-full py-2 z-50 gap-6">
            {/* Time - Current local time */}
            <div className="text-white font-bold text-lg tracking-wider">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>

            {/* Status Icons - Pure White */}
            <div className="flex items-center gap-6">
                <Wifi size={20} className="text-white" />
                <div className="flex items-center gap-2 text-white font-bold">
                    <span>{piBattery?.percent || 0}%</span>
                    <Battery size={20} className={piBattery?.state === 'Charging' ? 'text-green-500' : 'text-white'} />
                </div>
            </div>
        </div>
    );
};

export default Header;
