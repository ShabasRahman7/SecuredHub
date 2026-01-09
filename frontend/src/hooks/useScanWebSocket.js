import { useEffect, useState, useRef } from 'react';

const useScanWebSocket = (scanId) => {
    const [status, setStatus] = useState(null);
    const [progress, setProgress] = useState(0);
    const [message, setMessage] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [findingsCount, setFindingsCount] = useState(0);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const shouldReconnectRef = useRef(true);

    useEffect(() => {
        if (!scanId) return;

        const connect = () => {
            const token = localStorage.getItem('access_token');
            const wsUrl = `ws://localhost:8001/ws/scans/${scanId}/?token=${token}`;

            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                setIsConnected(true);
            };

            wsRef.current.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'scan_update' || data.type === 'scan_status') {
                    setStatus(data.status);
                    if (data.progress !== undefined) {
                        setProgress(data.progress);
                    }
                    if (data.message) {
                        setMessage(data.message);
                    }
                    if (data.findings_count !== undefined) {
                        setFindingsCount(data.findings_count);
                    }

                    if (data.status === 'completed' || data.status === 'failed') {
                        shouldReconnectRef.current = false;
                    }
                }
            };

            wsRef.current.onerror = (error) => {
                console.error('[WebSocket] Error:', error);
            };

            wsRef.current.onclose = () => {
                setIsConnected(false);
                if (shouldReconnectRef.current) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        connect();
                    }, 3000);
                }
            };
        };

        connect();

        return () => {
            shouldReconnectRef.current = false;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [scanId]);

    return { status, progress, message, isConnected, findingsCount };
};

export default useScanWebSocket;
