/**
 * Notification WebSocket Service
 * Handles real-time notifications via WebSocket connection
 */

class NotificationService {
    constructor() {
        this.ws = null;
        this.listeners = new Set();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.isConnected = false;
    }

    /**
     * Connect to the notification WebSocket
     * @param {string} token - JWT access token
     */
    connect(token) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        // derive WebSocket host from API URL
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';
        const apiHost = new URL(apiUrl).host;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${apiHost}/ws/notifications/?token=${token}`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this._notifyListeners({ type: 'connection', status: 'connected' });
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._notifyListeners(data);
                } catch (error) {
                    console.error('[NotificationService] Failed to parse message:', error);
                }
            };

            this.ws.onclose = (event) => {
                this.isConnected = false;
                this._notifyListeners({ type: 'connection', status: 'disconnected' });

                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this._scheduleReconnect(token);
                }
            };

            this.ws.onerror = () => {
                this._notifyListeners({ type: 'error', error: 'WebSocket error' });
            };
        } catch (error) {
            console.error('[NotificationService] Failed to connect:', error);
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnect');
            this.ws = null;
            this.isConnected = false;
        }
    }

    /**
     * Subscribe to notifications
     * @param {Function} callback - Function called when notification received
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback) {
        this.listeners.add(callback);
        return () => {
            this.listeners.delete(callback);
        };
    }

    /**
     * Send a ping to keep connection alive
     */
    ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        }
    }

    _notifyListeners(data) {
        this.listeners.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('[NotificationService] Listener error:', error);
            }
        });
    }

    _scheduleReconnect(token) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;

        setTimeout(() => {
            this.connect(token);
        }, delay);
    }
}

// export singleton instance
const notificationService = new NotificationService();
export default notificationService;
