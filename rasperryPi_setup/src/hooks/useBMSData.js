import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

/**
 * Custom hook to connect to BMS backend and receive real-time data
 * @param {string} serverUrl - Backend server URL (default: http://localhost:5000)
 * @returns {object} BMS data and connection status
 */
export const useBMSData = (serverUrl = 'http://localhost:5000') => {
    const [bmsData, setBmsData] = useState({
        temperature: 0,
        temperatures: [0, 0, 0, 0, 0],
        voltage: 0,
        current: 0,
        power: 0,
        soc: 0,
        soh: 0,
        battery_capacity: 0,
        charge_cycles: 0,
        charge_current: 0,
        remaining_time: 0,
        status: 'Connecting...',
        status_flags: [],
        last_update: 0,
        connected: false,
        speed_kmph: 0,
        speed_mode: 'ECONOMY',
        esp32_connected: false,
        pi_battery: {
            percent: 0,
            state: 'Unknown',
            voltage_mv: 0
        }
    });

    const [isConnected, setIsConnected] = useState(false);
    const socketRef = useRef(null);

    useEffect(() => {
        // Create socket connection
        const socket = io(serverUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 10
        });

        socketRef.current = socket;

        // Connection event handlers
        socket.on('connect', () => {
            console.log('✅ Connected to BMS server');
            setIsConnected(true);
            socket.emit('request_data'); // Request initial data
        });

        socket.on('disconnect', () => {
            console.log('❌ Disconnected from BMS server');
            setIsConnected(false);
        });

        socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            setIsConnected(false);
        });

        // BMS data update handler
        socket.on('bms_update', (data) => {
            console.log('📊 BMS data received:', data);
            setBmsData(data);
        });

        // Cleanup on unmount
        return () => {
            socket.disconnect();
        };
    }, [serverUrl]);

    // Manual refresh function
    const refresh = () => {
        if (socketRef.current && isConnected) {
            socketRef.current.emit('request_data');
        }
    };

    return {
        ...bmsData,
        isConnected,
        refresh
    };
};

export default useBMSData;
