import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001';

/**
 * WebSocket hook for real-time updates on compliance evaluations
 * @param {number|string} evaluationId - The evaluation ID to connect to
 * @param {object} options - Options object
 * @param {function} options.onMessage - Callback when message is received
 * @param {function} options.onConnect - Callback when connected
 * @param {function} options.onDisconnect - Callback when disconnected
 * @param {boolean} options.autoConnect - Auto connect on mount (default: true)
 */
export function useWebSocket(evaluationId, options = {}) {
    const { onMessage, onConnect, onDisconnect, autoConnect = true } = options;

    const [status, setStatus] = useState('disconnected');
    const [data, setData] = useState(null);
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
        if (!evaluationId) return;
        if (wsRef.current?.readyState === WebSocket.OPEN ||
            wsRef.current?.readyState === WebSocket.CONNECTING) return;

        const token = localStorage.getItem('access_token');
        const url = token
            ? `${WS_BASE_URL}/ws/evaluations/${evaluationId}/?token=${token}`
            : `${WS_BASE_URL}/ws/evaluations/${evaluationId}/`;

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
                    const parsed = JSON.parse(event.data);
                    setData(parsed);
                    callbacksRef.current.onMessage?.(parsed);
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
    }, [evaluationId]);

    const sendMessage = useCallback((message) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    }, []);

    useEffect(() => {
        if (autoConnect && evaluationId) {
            connect();
        }
        return () => disconnect();
    }, [evaluationId, autoConnect, connect, disconnect]);

    return {
        status,
        data,
        error,
        connect,
        disconnect,
        sendMessage,
        isConnected: status === 'connected',
    };
}

export default useWebSocket;
