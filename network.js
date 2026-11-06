/**
 * Poker Chess Network Layer (Zero-Dependency Vanilla JS)
 * Manages WebSocket connection, Lobby indexing, Room synchronization, and Reconnection.
 */

class NetworkClient {
    constructor() {
        this.ws = null;
        this.roomId = null;
        this.sessionToken = null;
        this.playerColor = null;
        this.isHost = false;
        this.isOnlineMatch = false;
        this.connectionStatus = 'offline'; // 'connected', 'reconnecting', 'offline'
        this.opponentConnected = true;
        this.opponentNickname = 'Opponent';

        this.listeners = {
            lobbyUpdate: [],
            roomJoined: [],
            setupStart: [],
            setupConfirmed: [],
            stateView: [],
            actionResult: [],
            opponentStatus: [],
            gameOver: [],
            error: [],
            connectionChange: []
        };

        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectTimer = null;
        this.cachedServerUrl = this.getDefaultServerUrl();
    }

    getDefaultServerUrl() {
        // Use local dev worker when running on localhost, otherwise cloudflare worker
        if (typeof window !== 'undefined' && window.location && window.location.hostname) {
            const host = window.location.hostname;
            if (host === 'localhost' || host === '127.0.0.1') {
                return 'ws://localhost:8787';
            }
        }
        return 'wss://poker-chess-server.laurence5kg.workers.dev';
    }

    getServerHttpUrl() {
        return this.cachedServerUrl.replace(/^ws/, 'http');
    }

    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(cb => {
                try { cb(data); } catch (e) { console.error('Network listener error:', e); }
            });
        }
    }

    // --- Lobby Connections ---

    async fetchPublicRooms() {
        try {
            const res = await fetch(`${this.getServerHttpUrl()}/api/rooms`, { method: 'GET' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.rooms || [];
        } catch (err) {
            console.warn('Cannot reach lobby HTTP API:', err.message);
            return null;
        }
    }

    connectLobby() {
        this.close();
        const wsUrl = `${this.cachedServerUrl}/lobby`;

        try {
            this.ws = new WebSocket(wsUrl);
            this.setupSocketHandlers('lobby');
        } catch (err) {
            this.emit('connectionChange', 'offline');
        }
    }

    // --- Room Connections ---

    connectRoom(roomId) {
        this.close();
        this.roomId = roomId;
        const wsUrl = `${this.cachedServerUrl}/room/${roomId}`;

        try {
            this.ws = new WebSocket(wsUrl);
            this.setupSocketHandlers('room');
        } catch (err) {
            this.emit('connectionChange', 'offline');
        }
    }

    setupSocketHandlers(mode) {
        if (!this.ws) return;

        this.ws.onopen = () => {
            this.connectionStatus = 'connected';
            this.reconnectAttempts = 0;
            this.emit('connectionChange', 'connected');
            this.startHeartbeat();

            // If we have an existing session for this room, attempt auto-reconnect
            if (mode === 'room' && this.sessionToken) {
                this.send('reconnect', { roomId: this.roomId, sessionToken: this.sessionToken });
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this.handleMessage(msg);
            } catch (err) {
                console.error('Failed to parse WS frame:', err);
            }
        };

        this.ws.onclose = (event) => {
            this.stopHeartbeat();
            if (this.connectionStatus === 'connected') {
                this.connectionStatus = 'reconnecting';
                this.emit('connectionChange', 'reconnecting');
                this.attemptReconnect(mode);
            } else {
                this.connectionStatus = 'offline';
                this.emit('connectionChange', 'offline');
            }
        };

        this.ws.onerror = (err) => {
            console.warn('WebSocket error:', err);
        };
    }

    attemptReconnect(mode) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.connectionStatus = 'offline';
            this.emit('connectionChange', 'offline');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 8000);
        clearTimeout(this.reconnectTimer);

        this.reconnectTimer = setTimeout(() => {
            if (mode === 'room' && this.roomId) {
                this.connectRoom(this.roomId);
            } else {
                this.connectLobby();
            }
        }, delay);
    }

    handleMessage(msg) {
        if (!msg || typeof msg !== 'object') return;

        switch (msg.type) {
            case 'lobby_update':
                this.emit('lobbyUpdate', msg.payload?.rooms || []);
                break;
            case 'room_joined':
                this.roomId = msg.payload.roomId;
                this.playerColor = msg.payload.playerColor;
                this.isHost = (msg.payload.role === 'host');
                this.sessionToken = msg.payload.sessionToken;
                this.isOnlineMatch = true;

                // Save session in sessionStorage
                try {
                    sessionStorage.setItem(`psj_session_${this.roomId}`, this.sessionToken);
                    sessionStorage.setItem(`psj_color_${this.roomId}`, this.playerColor);
                } catch (e) {}

                this.emit('roomJoined', msg.payload);
                break;
            case 'setup_start':
                this.opponentNickname = msg.payload.opponentNickname || 'Opponent';
                this.emit('setupStart', msg.payload);
                break;
            case 'setup_confirmed':
                this.emit('setupConfirmed', msg.payload);
                break;
            case 'state_view':
                this.emit('stateView', msg.payload);
                break;
            case 'action_result':
                this.emit('actionResult', msg.payload);
                break;
            case 'opponent_status':
                this.opponentConnected = msg.payload.connected;
                this.emit('opponentStatus', msg.payload);
                break;
            case 'game_over':
                this.emit('gameOver', msg.payload);
                break;
            case 'pong':
                this.lastPong = Date.now();
                break;
            case 'error':
                this.emit('error', msg.payload);
                break;
        }
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send('ping', { time: Date.now() });
            }
        }, 25000);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    send(type, payload = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return false;
        }
        // Auto-attach sessionToken and playerColor if available for bulletproof identification
        const enrichedPayload = { ...payload };
        if (this.sessionToken && !enrichedPayload.sessionToken) {
            enrichedPayload.sessionToken = this.sessionToken;
        }
        if (this.playerColor && !enrichedPayload.playerColor) {
            enrichedPayload.playerColor = this.playerColor;
        }
        const packet = JSON.stringify({ v: 1, type, payload: enrichedPayload });
        this.ws.send(packet);
        return true;
    }

    // --- Outbound Intent Methods ---

    createRoom(hostNickname, sidePreference = 'random') {
        const roomId = 'room_' + Math.random().toString(36).substring(2, 8);
        this.connectRoom(roomId);

        // Send create_room once socket opens
        const sendCreate = () => {
            this.send('create_room', { roomId, hostNickname, sidePreference });
        };

        if (this.ws.readyState === WebSocket.OPEN) {
            sendCreate();
        } else {
            this.ws.addEventListener('open', sendCreate, { once: true });
        }
    }

    joinRoom(roomId, nickname) {
        this.connectRoom(roomId);

        const sendJoin = () => {
            this.send('join_room', { roomId, nickname });
        };

        if (this.ws.readyState === WebSocket.OPEN) {
            sendJoin();
        } else {
            this.ws.addEventListener('open', sendJoin, { once: true });
        }
    }

    submitLayout(camp, reserves) {
        return this.send('submit_layout', {
            camp,
            reserves,
            sessionToken: this.sessionToken,
            playerColor: this.playerColor
        });
    }

    sendAction(action) {
        return this.send('action', {
            ...action,
            sessionToken: this.sessionToken,
            playerColor: this.playerColor
        });
    }

    sendForfeit() {
        return this.send('forfeit', {
            sessionToken: this.sessionToken,
            playerColor: this.playerColor
        });
    }

    close() {
        this.stopHeartbeat();
        clearTimeout(this.reconnectTimer);
        if (this.ws) {
            this.ws.onclose = null;
            this.ws.onerror = null;
            this.ws.close();
            this.ws = null;
        }
        this.connectionStatus = 'offline';
    }

    resetMatch() {
        this.close();
        this.roomId = null;
        this.sessionToken = null;
        this.playerColor = null;
        this.isHost = false;
        this.isOnlineMatch = false;
        this.opponentConnected = true;
    }
}

// Global instance
if (typeof window !== 'undefined') {
    window.networkClient = new NetworkClient();
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NetworkClient };
}
