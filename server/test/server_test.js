/**
 * Comprehensive Server Unit Tests for Poker Chess Online Backend
 * Executed via Node.js native test runner: `node --test`
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { RoomDO } from '../RoomDO.js';
import { LobbyDO } from '../LobbyDO.js';
import { GameEngine, Card } from '../../game.js';

// Mock WebSocket helper for testing
class MockWebSocket {
    constructor(id) {
        this.id = id;
        this.sent = [];
        this.listeners = {};
    }

    send(data) {
        this.sent.push(typeof data === 'string' ? JSON.parse(data) : data);
    }

    addEventListener(event, fn) {
        this.listeners[event] = fn;
    }

    close() {
        if (this.listeners['close']) this.listeners['close']();
    }

    lastMessage() {
        return this.sent[this.sent.length - 1] || null;
    }

    messagesOfType(type) {
        return this.sent.filter(m => m.type === type);
    }
}

// Mock DurableObjectState
function createMockState() {
    const store = new Map();
    return {
        storage: {
            get: async (k) => store.get(k),
            put: async (k, v) => store.set(k, v),
            delete: async (k) => store.delete(k)
        },
        blockConcurrencyWhile: async (fn) => fn(),
        getWebSockets: () => []
    };
}

// Helper to generate a valid 25 camp + 2 reserve layout
function generateValidLayout(color) {
    const engine = new GameEngine();
    engine.initSetup(color);
    engine.autoSetup(color);

    const minRow = color === 'red' ? 0 : 7;
    const maxRow = color === 'red' ? 4 : 11;

    const camp = [];
    for (let r = minRow; r <= maxRow; r++) {
        for (let c = 0; c < 5; c++) {
            const card = engine.board[r][c];
            camp.push({ r, c, rank: card.rank, suit: card.suit });
        }
    }
    const reserves = engine.hands[color].startingReserves.map(c => ({
        rank: c.rank,
        suit: c.suit
    }));

    return { camp, reserves };
}

test('1. View-Projection Leak Test: Strict Fog-of-War Enforcement', async (t) => {
    const room = new RoomDO(createMockState(), {});
    const wsRed = new MockWebSocket('ws_red');
    const wsBlack = new MockWebSocket('ws_black');

    room.setupWebSocketListeners(wsRed);
    room.setupWebSocketListeners(wsBlack);

    // Host creates room as Red
    await room.handleCreateRoom(wsRed, { hostNickname: 'HostRed', sidePreference: 'red' });
    assert.equal(room.players.red.role, 'host');

    // Guest joins as Black
    await room.handleJoinRoom(wsBlack, { nickname: 'GuestBlack' });
    assert.equal(room.players.black.role, 'guest');
    assert.equal(room.gameState, 'setup');

    // Submit validated layouts
    const redLayout = generateValidLayout('red');
    const blackLayout = generateValidLayout('black');

    await room.handleSubmitLayout(wsRed, redLayout);
    await room.handleSubmitLayout(wsBlack, blackLayout);

    assert.equal(room.gameState, 'playing');
    assert.equal(room.currentTurn, 'red');

    // Test View Projection for Red
    const redView = room.projectStateView('red');
    const redViewJson = JSON.stringify(redView);

    // 1. Red must see own cards with ranks
    assert.ok(redView.payload.board[0][0].rank !== null, 'Red should see own card rank');
    assert.equal(redView.payload.hands.red.startingReserves.length, 2, 'Red should see own reserves');

    // 2. Red must NEVER receive unrevealed Black ranks or suits
    const blackCampRows = [7, 8, 9, 10, 11];
    for (const r of blackCampRows) {
        for (let c = 0; c < 5; c++) {
            const piece = redView.payload.board[r][c];
            if (piece) {
                assert.equal(piece.player, 'black');
                assert.equal(piece.rank, null, `Opponent card at (${r},${c}) must have rank === null`);
                assert.equal(piece.suit, null, `Opponent card at (${r},${c}) must have suit === null`);
                assert.equal(piece.isFlag, false, `Opponent card at (${r},${c}) must not leak isFlag`);
                assert.equal(piece.isBomb, false, `Opponent card at (${r},${c}) must not leak isBomb`);
                assert.equal(piece.isLandmine, false, `Opponent card at (${r},${c}) must not leak isLandmine`);
            }
        }
    }

    // 3. Black starting reserves must NOT be transmitted in Red's view
    assert.equal(redView.payload.hands.black.startingReserves.length, 0, 'Opponent reserves array must be empty');
    assert.equal(redView.payload.hands.black.startingReserveCount, 2, 'Opponent reserve count must be accurate');

    // 4. Assert that Black's secret reserves do not appear anywhere in serialized JSON
    for (const reserveCard of blackLayout.reserves) {
        const secretFragment = `"rank":"${reserveCard.rank}","suit":"${reserveCard.suit}"`;
        // Only if it doesn't match Red's own reserves
        const appearsInRedReserves = redLayout.reserves.some(r => r.rank === reserveCard.rank && r.suit === reserveCard.suit);
        if (!appearsInRedReserves) {
            assert.ok(!redViewJson.includes(secretFragment), `Secret reserve ${secretFragment} leaked in serialized JSON!`);
        }
    }

    // Test View Projection for Black
    const blackView = room.projectStateView('black');
    assert.equal(blackView.payload.hands.black.startingReserves.length, 2);
    assert.equal(blackView.payload.hands.red.startingReserves.length, 0);
    assert.equal(blackView.payload.board[0][0].rank, null, 'Black must not see Red rank');
});

test('2. Forged and Illegal Action Tests: Zero Trust Enforcement', async (t) => {
    const room = new RoomDO(createMockState(), {});
    const wsRed = new MockWebSocket('ws_red');
    const wsBlack = new MockWebSocket('ws_black');
    room.setupWebSocketListeners(wsRed);
    room.setupWebSocketListeners(wsBlack);

    await room.handleCreateRoom(wsRed, { hostNickname: 'HostRed', sidePreference: 'red' });
    await room.handleJoinRoom(wsBlack, { nickname: 'GuestBlack' });
    await room.handleSubmitLayout(wsRed, generateValidLayout('red'));
    await room.handleSubmitLayout(wsBlack, generateValidLayout('black'));

    // Attempt 1: Forged move with invalid coordinates
    wsRed.sent = [];
    await room.handlePlayerAction(wsRed, { type: 'move', from: { r: 99, c: 99 }, to: { r: 100, c: 100 } });
    let last = wsRed.lastMessage();
    assert.equal(last?.type, 'error');
    assert.equal(last?.payload?.code, 'ILLEGAL_ACTION');

    // Attempt 2: Forged move of opponent's piece
    wsRed.sent = [];
    await room.handlePlayerAction(wsRed, { type: 'move', from: { r: 7, c: 0 }, to: { r: 6, c: 0 } });
    last = wsRed.lastMessage();
    assert.equal(last?.type, 'error');
    assert.equal(last?.payload?.code, 'ILLEGAL_ACTION');

    // Attempt 3: Forged illegal drop into non-camp tile
    wsRed.sent = [];
    await room.handlePlayerAction(wsRed, { type: 'drop', handType: 'starting', index: 0, to: { r: 6, c: 2 } });
    last = wsRed.lastMessage();
    assert.equal(last?.type, 'error');
    assert.equal(last?.payload?.code, 'ILLEGAL_ACTION');

    // Engine current turn must remain Red
    assert.equal(room.currentTurn, 'red');
});

test('3. Out-of-Turn Action Rejection', async (t) => {
    const room = new RoomDO(createMockState(), {});
    const wsRed = new MockWebSocket('ws_red');
    const wsBlack = new MockWebSocket('ws_black');
    room.setupWebSocketListeners(wsRed);
    room.setupWebSocketListeners(wsBlack);

    await room.handleCreateRoom(wsRed, { hostNickname: 'HostRed', sidePreference: 'red' });
    await room.handleJoinRoom(wsBlack, { nickname: 'GuestBlack' });
    await room.handleSubmitLayout(wsRed, generateValidLayout('red'));
    await room.handleSubmitLayout(wsBlack, generateValidLayout('black'));

    // Red's turn currently. Black attempts to move out of turn!
    assert.equal(room.currentTurn, 'red');
    wsBlack.sent = [];
    await room.handlePlayerAction(wsBlack, { type: 'move', from: { r: 7, c: 0 }, to: { r: 6, c: 0 } });

    const err = wsBlack.lastMessage();
    assert.equal(err?.type, 'error');
    assert.equal(err?.payload?.code, 'NOT_YOUR_TURN');
    assert.equal(room.currentTurn, 'red', 'Turn must not advance on out-of-turn attempt');
});

test('4. Disconnect, Reconnect & Session Recovery Test', async (t) => {
    const room = new RoomDO(createMockState(), {});
    const wsRed = new MockWebSocket('ws_red');
    const wsBlack = new MockWebSocket('ws_black');
    room.setupWebSocketListeners(wsRed);
    room.setupWebSocketListeners(wsBlack);

    await room.handleCreateRoom(wsRed, { hostNickname: 'HostRed', sidePreference: 'red' });
    await room.handleJoinRoom(wsBlack, { nickname: 'GuestBlack' });
    await room.handleSubmitLayout(wsRed, generateValidLayout('red'));
    await room.handleSubmitLayout(wsBlack, generateValidLayout('black'));

    const redToken = room.players.red.sessionToken;
    assert.ok(redToken, 'Red should have valid session token');

    // Red drops connection
    wsBlack.sent = [];
    room.handlePlayerDisconnect(wsRed);
    assert.equal(room.players.red.connected, false);

    // Opponent Black receives disconnect notice with grace period
    const statusMsg = wsBlack.messagesOfType('opponent_status')[0];
    assert.ok(statusMsg, 'Black should receive opponent_status');
    assert.equal(statusMsg.payload.connected, false);
    assert.equal(statusMsg.payload.gracePeriodRemainingMs, 60000);

    // Red reconnects with invalid token
    const wsRedNew = new MockWebSocket('ws_red_new');
    room.setupWebSocketListeners(wsRedNew);
    await room.handleReconnect(wsRedNew, { sessionToken: 'wrong_token_123' });
    let res = wsRedNew.lastMessage();
    assert.equal(res?.type, 'error');
    assert.equal(res?.payload?.code, 'SESSION_NOT_FOUND');

    // Red reconnects with valid token
    wsRedNew.sent = [];
    wsBlack.sent = [];
    await room.handleReconnect(wsRedNew, { sessionToken: redToken });

    assert.equal(room.players.red.connected, true);
    assert.equal(room.players.red.ws, wsRedNew);

    // Reconnected player receives room_joined and immediate state_view
    const roomJoined = wsRedNew.messagesOfType('room_joined')[0];
    assert.ok(roomJoined);
    assert.equal(roomJoined.payload.playerColor, 'red');

    const stateView = wsRedNew.messagesOfType('state_view')[0];
    assert.ok(stateView);
    assert.equal(stateView.payload.yourSide, 'red');

    // Opponent Black receives reconnection notice
    const oppReturn = wsBlack.messagesOfType('opponent_status')[0];
    assert.ok(oppReturn);
    assert.equal(oppReturn.payload.connected, true);
});

test('5. Forfeit and Timeout Tests', async (t) => {
    // 5a. Explicit Forfeit
    const roomA = new RoomDO(createMockState(), {});
    const wsRedA = new MockWebSocket('ws_red_a');
    const wsBlackA = new MockWebSocket('ws_black_a');
    roomA.setupWebSocketListeners(wsRedA);
    roomA.setupWebSocketListeners(wsBlackA);

    await roomA.handleCreateRoom(wsRedA, { hostNickname: 'HostRed', sidePreference: 'red' });
    await roomA.handleJoinRoom(wsBlackA, { nickname: 'GuestBlack' });
    await roomA.handleSubmitLayout(wsRedA, generateValidLayout('red'));
    await roomA.handleSubmitLayout(wsBlackA, generateValidLayout('black'));

    wsBlackA.sent = [];
    await roomA.handleForfeit(wsRedA);

    assert.equal(roomA.gameState, 'finished');
    assert.equal(roomA.winner, 'black');
    const gameOverA = wsBlackA.messagesOfType('game_over')[0];
    assert.ok(gameOverA);
    assert.equal(gameOverA.payload.winner, 'black');
    assert.equal(gameOverA.payload.forfeitedBy, 'red');

    // 5b. Disconnect Grace Period Expiration (Abandonment)
    const roomB = new RoomDO(createMockState(), {});
    const wsRedB = new MockWebSocket('ws_red_b');
    const wsBlackB = new MockWebSocket('ws_black_b');
    roomB.setupWebSocketListeners(wsRedB);
    roomB.setupWebSocketListeners(wsBlackB);

    await roomB.handleCreateRoom(wsRedB, { hostNickname: 'HostRed', sidePreference: 'red' });
    await roomB.handleJoinRoom(wsBlackB, { nickname: 'GuestBlack' });
    await roomB.handleSubmitLayout(wsRedB, generateValidLayout('red'));
    await roomB.handleSubmitLayout(wsBlackB, generateValidLayout('black'));

    wsRedB.sent = [];
    // Black disconnects and grace period expires
    roomB.handleAbandonment('black');

    assert.equal(roomB.gameState, 'finished');
    assert.equal(roomB.winner, 'red');
    const gameOverB = wsRedB.messagesOfType('game_over')[0];
    assert.ok(gameOverB);
    assert.equal(gameOverB.payload.winner, 'red');
    assert.equal(gameOverB.payload.forfeitedBy, 'black');
});

test('6. LobbyDO: Room Indexing, Pruning & Capacity', async (t) => {
    const lobby = new LobbyDO(createMockState(), {});

    // Create 3 rooms
    await lobby.fetch(new Request('http://localhost/register', {
        method: 'POST',
        body: JSON.stringify({ roomId: 'r1', hostNickname: 'Alpha', sidePreference: 'red' })
    }));
    await lobby.fetch(new Request('http://localhost/register', {
        method: 'POST',
        body: JSON.stringify({ roomId: 'r2', hostNickname: 'Beta', sidePreference: 'black' })
    }));
    await lobby.fetch(new Request('http://localhost/register', {
        method: 'POST',
        body: JSON.stringify({ roomId: 'r3', hostNickname: 'Gamma', sidePreference: 'random' })
    }));

    const res = await lobby.fetch(new Request('http://localhost/api/rooms', { method: 'GET' }));
    const data = await res.json();
    assert.equal(data.rooms.length, 3);
    assert.equal(data.rooms[0].roomId, 'r3'); // Newest first

    // Unregister r2
    await lobby.fetch(new Request('http://localhost/unregister', {
        method: 'POST',
        body: JSON.stringify({ roomId: 'r2' })
    }));

    const res2 = await lobby.fetch(new Request('http://localhost/api/rooms', { method: 'GET' }));
    const data2 = await res2.json();
    assert.equal(data2.rooms.length, 2);
    assert.ok(!data2.rooms.some(r => r.roomId === 'r2'));
});
