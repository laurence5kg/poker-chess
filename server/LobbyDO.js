/**
 * LobbyDO: Singleton Durable Object for Public Matchmaking & Room Discovery
 * Supports Cloudflare Workers WebSocket Hibernation API and HTTP polling.
 */

export class LobbyDO {
    constructor(state, env) {
        this.state = state;
        this.env = env;
        this.rooms = new Map(); // roomId -> { roomId, hostNickname, sidePreference, createdAt, seq, status }
        this.MAX_ROOMS = 100;
        this.ROOM_TTL_MS = 10 * 60 * 1000; // 10 minutes
        this.seq = 0;
    }

    async fetch(request) {
        const url = new URL(request.url);

        // 1. WebSocket connection to /lobby for real-time broadcasts
        if (request.headers.get('Upgrade')?.toLowerCase() === 'websocket') {
            const pair = new WebSocketPair();
            const [client, server] = Object.values(pair);

            if (this.state.acceptWebSocket) {
                this.state.acceptWebSocket(server);
            } else {
                server.accept();
            }

            // Clean expired rooms and send current list immediately
            this.pruneExpiredRooms();
            server.send(JSON.stringify({
                v: 1,
                type: 'lobby_update',
                payload: { rooms: this.getPublicRooms() }
            }));

            return new Response(null, { status: 101, webSocket: client });
        }

        // 2. HTTP GET /api/rooms: polling fallback
        if (request.method === 'GET') {
            this.pruneExpiredRooms();
            return new Response(JSON.stringify({
                v: 1,
                rooms: this.getPublicRooms()
            }), {
                headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
            });
        }

        // 3. Internal room register: POST /register
        if (request.method === 'POST' && url.pathname.endsWith('/register')) {
            const data = await request.json();
            if (this.rooms.size >= this.MAX_ROOMS) {
                return new Response(JSON.stringify({ error: 'MAX_ROOMS_REACHED' }), { status: 429 });
            }
            this.seq += 1;
            this.rooms.set(data.roomId, {
                roomId: data.roomId,
                hostNickname: this.sanitizeNickname(data.hostNickname),
                sidePreference: data.sidePreference || 'random',
                createdAt: Date.now(),
                seq: this.seq,
                status: 'waiting'
            });
            this.broadcastLobbyUpdate();
            return new Response(JSON.stringify({ ok: true }));
        }

        // 4. Internal room unregister: POST /unregister
        if (request.method === 'POST' && url.pathname.endsWith('/unregister')) {
            const data = await request.json();
            if (this.rooms.has(data.roomId)) {
                this.rooms.delete(data.roomId);
                this.broadcastLobbyUpdate();
            }
            return new Response(JSON.stringify({ ok: true }));
        }

        return new Response('Not Found', { status: 404 });
    }

    sanitizeNickname(name) {
        if (!name || typeof name !== 'string') return 'Player';
        const cleaned = name.trim().replace(/[^a-zA-Z0-9_\u4e00-\u9fa5 -]/g, '').slice(0, 16);
        return cleaned || 'Player';
    }

    pruneExpiredRooms() {
        const now = Date.now();
        for (const [id, room] of this.rooms.entries()) {
            if (now - room.createdAt > this.ROOM_TTL_MS) {
                this.rooms.delete(id);
            }
        }
    }

    getPublicRooms() {
        this.pruneExpiredRooms();
        return Array.from(this.rooms.values())
            .filter(r => r.status === 'waiting')
            .sort((a, b) => {
                if (b.createdAt !== a.createdAt) return b.createdAt - a.createdAt;
                return b.seq - a.seq;
            });
    }

    broadcastLobbyUpdate() {
        const msg = JSON.stringify({
            v: 1,
            type: 'lobby_update',
            payload: { rooms: this.getPublicRooms() }
        });

        const websockets = this.state.getWebSockets ? this.state.getWebSockets() : [];
        for (const ws of websockets) {
            try {
                ws.send(msg);
            } catch (err) {
                // Stale connection will be cleaned up
            }
        }
    }

    // Cloudflare WebSocket Hibernation event handlers
    async webSocketMessage(ws, message) {
        try {
            const data = JSON.parse(message);
            if (data.type === 'list_rooms') {
                ws.send(JSON.stringify({
                    v: 1,
                    type: 'lobby_update',
                    payload: { rooms: this.getPublicRooms() }
                }));
            }
        } catch (e) {
            // Ignore malformed ping/text
        }
    }

    async webSocketClose(ws, code, reason, wasClean) {
        // Automatically handled by hibernation API
    }
}
