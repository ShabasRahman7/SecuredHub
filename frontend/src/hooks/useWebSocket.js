import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001';

export function useWebSocket(scanId, options = {}) {
    const { onMessage, onConnect, onDisconnect, autoConnect = true } = options;
    
    const [status, setStatus] = useState('disconnected');
    const [scanData, setScanData] = useState(null);
    const [error, setError] = useState(null);
    const wsRef = useRef(null);
    const callbacksRef = useRef({ onMessage, onConnect, onDisconnect });

    useEffect(() => {
        callbacksRef.current = { onMessage, onConnect, onDisconnect };
    }, [onMessage, onConnect, onDisconnect]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setStatus('disconnected');
    }, []);

    const connect = useCallback(() => {
        if (!scanId) return;
        if (wsRef.current?.readyState === WebSocket.OPEN || 
            wsRef.current?.readyState === WebSocket.CONNECTING) return;

        const token = localStorage.getItem('access_token');
        const url = token 
            ? `${WS_BASE_URL}/ws/scans/${scanId}/?token=${token}`
            : `${WS_BASE_URL}/ws/scans/${scanId}/`;
        
        try {
            wsRef.current = new WebSocket(url);
            setStatus('connecting');
            setError(null);

            wsRef.current.onopen = () => {
                setStatus('connected');
                callbacksRef.current.onConnect?.();
            };

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setScanData(data);
                    callbacksRef.current.onMessage?.(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            wsRef.current.onclose = () => {
                setStatus('disconnected');
                wsRef.current = null;
                callbacksRef.current.onDisconnect?.();
            };

            wsRef.current.onerror = () => {
                setError('WebSocket connection failed');
                setStatus('error');
            };
        } catch (e) {
            setError(e.message);
            setStatus('error');
        }
    }, [scanId]);

    const sendMessage = useCallback((message) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    }, []);

    useEffect(() => {
        if (autoConnect && scanId) {
            connect();
        }
        return () => disconnect();
    }, [scanId, autoConnect, connect, disconnect]);

    return {
        status,
        scanData,
        error,
        connect,
        disconnect,
        sendMessage,
        isConnected: status === 'connected',
    };
}

export default useWebSocket;
