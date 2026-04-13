import React, { useEffect } from 'react';
import { useVehicleStore } from '../store/useVehicleStore';
import DashboardEngine from '../engine/DashboardEngine';
import * as Icons from 'lucide-react';

const Dashboard = () => {
  const { initialize, isInitialized, connectionStatus, cleanup } = useVehicleStore();

  useEffect(() => {
    // Initializing with default vehicle, config system can load from url if needed.
    initialize('default');
    
    return () => {
      cleanup();
    };
  }, [initialize, cleanup]);

  if (!isInitialized) {
    return (
      <div className="flex h-full min-h-0 items-center justify-center flex-col gap-4">
        <Icons.Loader2 className="animate-spin text-dashboard-accent" size={48} />
        <span className="text-dashboard-muted font-mono tracking-widest text-sm uppercase">INIT CORE SYSTEM</span>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full min-h-0 overflow-hidden">
      
      {/* Background Decor Elements */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-dashboard-accent/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />
      
      {/* Network Status Overlay */}
      {connectionStatus !== 'CONNECTED' && (
        <div className="absolute top-3 right-4 z-50 flex items-center gap-2 bg-dashboard-panel/80 px-3 py-1.5 rounded-full border border-dashboard-panelBorder backdrop-blur-sm">
          <Icons.WifiOff className="text-dashboard-danger" size={14} />
          <span className="text-dashboard-danger text-xs font-bold tracking-widest">
            {connectionStatus}
          </span>
        </div>
      )}

      {/* Dynamic Engine */}
      <div className="w-full h-full min-h-0 relative z-10">
         <DashboardEngine />
      </div>
    </div>
  );
};

export default Dashboard;
