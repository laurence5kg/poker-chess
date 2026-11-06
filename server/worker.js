/**
 * Cloudflare Worker Entrypoint for Poker Chess Online PvP
 * Handles CORS, Origin Allow-List, and WebSocket Upgrades to Durable Objects.
 */

import { LobbyDO } from './LobbyDO.js';
import { RoomDO } from './RoomDO.js';

export { LobbyDO, RoomDO };

const ALLOWED_ORIGIN_PATTERNS = [
    /^https:\/\/laurence5kg\.github\.io$/,
    /^http:\/\/localhost(:\d+)?$/,
    /^http:\/\/127\.0\.0\.1(:\d+)?$/
];

function isOriginAllowed(origin) {
    if (!origin) return true; // Direct/non-browser requests allowed in dev/testing
    return ALLOWED_ORIGIN_PATTERNS.some(pattern => pattern.test(origin));
}

function corsHeaders(origin) {
    return {
        'Access-Control-Allow-Origin': origin || '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Upgrade',
    };
}

export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const origin = request.headers.get('Origin');

        // 1. Origin verification
        if (!isOriginAllowed(origin)) {
            return new Response('Forbidden: Origin not allowed', { status: 403 });
        }

        // 2. Handle CORS preflight
        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders(origin) });
        }

        // 3. Health check
        if (url.pathname === '/health' || url.pathname === '/api/health') {
            return new Response(JSON.stringify({ status: 'ok', v: 1 }), {
                headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) }
            });
        }

        // 4. Lobby routes
        if (url.pathname === '/api/rooms' || url.pathname === '/lobby') {
            if (!env.LOBBY_DO) {
                return new Response(JSON.stringify({ error: 'Lobby DO not bound' }), { status: 500 });
            }
            const lobbyId = env.LOBBY_DO.idFromName('global-lobby');
            const lobbyStub = env.LOBBY_DO.get(lobbyId);
            return lobbyStub.fetch(request);
        }

        // 5. Room routes: /room/:roomId
        const roomMatch = url.pathname.match(/^\/room\/([a-zA-Z0-9_-]{4,32})$/);
        if (roomMatch) {
            const roomId = roomMatch[1];
            if (!env.ROOM_DO) {
                return new Response(JSON.stringify({ error: 'Room DO not bound' }), { status: 500 });
            }
            const roomDoId = env.ROOM_DO.idFromName(roomId);
            const roomStub = env.ROOM_DO.get(roomDoId);
            return roomStub.fetch(request);
        }

        return new Response('Not Found', { status: 404, headers: corsHeaders(origin) });
    }
};
