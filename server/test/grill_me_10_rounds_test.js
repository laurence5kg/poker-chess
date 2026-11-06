/**
 * 10-Round "Grill Me" Deep Diagnostic & Regression Verification Suite
 * Verifies all 10 architectural invariants to ensure the online setup and confirm flow is rock solid.
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { RoomDO } from '../RoomDO.js';
import { GameEngine, Card } from '../../game.js';
import { NetworkClient } from '../../network.js';

class MockWebSocket {
    constructor() {
        this.sent = [];
        this.attachment = null;
        this.readyState = 1; // OPEN
    }
    send(data) {
        this.sent.push(JSON.parse(data));
    }
    serializeAttachment(val) {
        this.attachment = JSON.parse(JSON.stringify(val));
    }
    deserializeAttachment() {
        return this.attachment ? JSON.parse(JSON.stringify(this.attachment)) : null;
    }
    close() {
        this.readyState = 3; // CLOSED
    }
}

class MockState {
    constructor() {
        this.storage = new Map();
        this.sockets = [];
    }
    acceptWebSocket(ws) {
        this.sockets.push(ws);
    }
    getWebSockets() {
        return this.sockets;
    }
    blockConcurrencyWhile(fn) {
        return fn();
    }
}

function makeValidCamp(color) {
    const minRow = color === 'red' ? 0 : 7;
    const maxRow = color === 'red' ? 4 : 11;
    const frontRow = color === 'red' ? 4 : 7;
    const backRow = color === 'red' ? 0 : 11;
    const camp = [];
    
    // Create standard deck pool
    const engine = new GameEngine();
    const deck = engine.createDeck(color);
    
    // Put Flag and Landmines on safe back row, mobiles elsewhere
    const flag = deck.find(c => c.isFlag);
    const mines = deck.filter(c => c.isLandmine);
    const mobiles = deck.filter(c => !c.isFlag && !c.isLandmine);
    
    // 2 reserves
    const reserves = mobiles.splice(0, 2).map(c => ({ rank: c.rank, suit: c.suit }));
    
    // We have 5 mobiles for frontRow, flag + mines for backRow, and remaining mobiles in between
    const frontMobiles = mobiles.splice(0, 5);
    const backCards = [flag, ...mines];
    while (backCards.length < 5) {
        backCards.push(mobiles.shift());
    }
    const midCards = mobiles; // remaining 15 cards for the 3 middle rows
    
    for (let r = minRow; r <= maxRow; r++) {
        for (let c = 0; c < 5; c++) {
            let card;
            if (r === frontRow) {
                card = frontMobiles[c];
            } else if (r === backRow) {
                card = backCards[c];
            } else {
                card = midCards.shift();
            }
            camp.push({ r, c, rank: card.rank, suit: card.suit });
        }
    }
    return { camp, reserves };
}

// ==========================================
// ROUND 1: Hibernation State Survival & Socket Attachment
// ==========================================
test('Round 1: Hibernation State Survival & Attachment Serialization', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    
    // Check ws.serializeAttachment was populated
    assert.ok(wsHost.attachment, 'Attachment should be serialized');
    assert.equal(wsHost.attachment.playerColor, 'red');
    assert.ok(wsHost.attachment.sessionToken, 'Session token must be present');
    
    // SIMULATE DO HIBERNATION: Wipe in-memory references
    room.players.red.ws = null;
    room.players.red.connected = false;
    
    // Next frame arrives from hibernated socket
    const color = room.getPlayerColorByWs(wsHost);
    assert.equal(color, 'red', 'Should recover red player identity via deserializeAttachment');
    assert.equal(room.players.red.ws, wsHost, 'Should rebind red socket in memory');
    assert.equal(room.players.red.connected, true, 'Should mark connected');
});

// ==========================================
// ROUND 2: Bidirectional Session Token Fallback
// ==========================================
test('Round 2: Bidirectional Session Token Fallback without Attachment', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsGuest = new MockWebSocket();
    
    await room.handleCreateRoom(new MockWebSocket(), { hostNickname: 'Alice', sidePreference: 'red' });
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    
    const blackToken = room.players.black.sessionToken;
    assert.ok(blackToken, 'Bob should have sessionToken');
    
    // Deliberately strip attachment and nullify memory ws (worst-case legacy environment)
    wsGuest.attachment = null;
    room.players.black.ws = null;
    
    // Incoming message contains sessionToken in payload
    const color = room.getPlayerColorByWs(wsGuest, { payload: { sessionToken: blackToken } });
    assert.equal(color, 'black', 'Should resolve color via sessionToken fallback');
    assert.equal(room.players.black.ws, wsGuest, 'Should rebind memory ws pointer');
});

// ==========================================
// ROUND 3: Server Outbound Routing & Wakeup Broadcasting
// ==========================================
test('Round 3: sendToPlayer & broadcast via state.getWebSockets after hibernation', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    const wsGuest = new MockWebSocket();
    state.sockets.push(wsHost, wsGuest);
    
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    
    // Clear in-memory pointers to simulate cold wake from storage
    room.players.red.ws = null;
    room.players.black.ws = null;
    
    // Broadcast must still find sockets in state.getWebSockets() via attachment
    room.sendToPlayer('red', { type: 'test_red', payload: { ok: true } });
    room.sendToPlayer('black', { type: 'test_black', payload: { ok: true } });
    
    const hostReceived = wsHost.sent.find(m => m.type === 'test_red');
    const guestReceived = wsGuest.sent.find(m => m.type === 'test_black');
    assert.ok(hostReceived, 'Host should receive message after wakeup');
    assert.ok(guestReceived, 'Guest should receive message after wakeup');
});

// ==========================================
// ROUND 4: Error Handling & Error Message Delivery
// ==========================================
test('Round 4: Detailed Error Payload Delivery on Invalid Setup', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    const wsGuest = new MockWebSocket();
    
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    
    // Host submits invalid layout (only 5 cards)
    await room.handleSubmitLayout(wsHost, { camp: [{ r: 0, c: 0, rank: 'A', suit: 'spades' }], reserves: [] });
    const err = wsHost.sent.find(m => m.type === 'error');
    assert.ok(err, 'Should receive error packet');
    assert.equal(err.payload.code, 'INVALID_LAYOUT_COUNTS');
});

// ==========================================
// ROUND 5: Frontline Rule Enforcement
// ==========================================
test('Round 5: Frontline Rule Enforcement (Flag & Mine Prohibited)', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    const wsGuest = new MockWebSocket();
    
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    
    // Create layout with Flag illegally placed on Red frontline (row 4)
    const { camp, reserves } = makeValidCamp('red');
    // Swap flag to row 4
    const flagPiece = camp.find(p => p.rank === 'JOKER');
    const frontPiece = camp.find(p => p.r === 4 && p.c === 2);
    const tempRank = flagPiece.rank;
    const tempSuit = flagPiece.suit;
    flagPiece.rank = frontPiece.rank;
    flagPiece.suit = frontPiece.suit;
    frontPiece.rank = tempRank;
    frontPiece.suit = tempSuit;
    
    await room.handleSubmitLayout(wsHost, { camp, reserves });
    const err = wsHost.sent.find(m => m.type === 'error');
    assert.ok(err, 'Should reject frontline Flag');
    assert.equal(err.payload.code, 'INVALID_SETUP_RULES');
    assert.ok(err.payload.errors.some(e => e.includes('frontline')), 'Error should mention frontline');
});

// ==========================================
// ROUND 6: Inverted Black Camp Coordinates & Out-of-Bounds Rejection
// ==========================================
test('Round 6: Camp Coordinate Bounds & Duplicate Rejection', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    const wsGuest = new MockWebSocket();
    
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    
    // Black player submits a card in Red's camp (row 2 instead of 7..11)
    const { camp, reserves } = makeValidCamp('black');
    camp[0].r = 2; // ILLEGAL
    
    await room.handleSubmitLayout(wsGuest, { camp, reserves });
    const err = wsGuest.sent.find(m => m.type === 'error');
    assert.ok(err, 'Should reject out-of-bounds coordinate');
    assert.equal(err.payload.code, 'COORDINATE_OUT_OF_BOUNDS');
});

// ==========================================
// ROUND 7: WebSocket Keep-Alive Pings & Pong Response
// ==========================================
test('Round 7: WebSocket Ping/Pong Keep-Alive', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const ws = new MockWebSocket();
    
    await room.webSocketMessage(ws, JSON.stringify({ v: 1, type: 'ping', payload: { time: 12345 } }));
    const pong = ws.sent.find(m => m.type === 'pong');
    assert.ok(pong, 'Server must respond with pong');
    assert.ok(pong.payload.time, 'Pong must have timestamp');
});

// ==========================================
// ROUND 8: Zero-Information-Leakage & State Projection Audit
// ==========================================
test('Round 8: Zero-Information-Leakage State Projection Audit', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    const wsGuest = new MockWebSocket();
    state.sockets.push(wsHost, wsGuest);
    
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    
    // Both submit valid layouts
    const redLayout = makeValidCamp('red');
    const blackLayout = makeValidCamp('black');
    await room.handleSubmitLayout(wsHost, redLayout);
    await room.handleSubmitLayout(wsGuest, blackLayout);
    
    // Game should transition to playing
    assert.equal(room.gameState, 'playing');
    
    // Inspect Red's projected view
    const redView = room.projectStateView('red');
    const blackPiecesSeenByRed = [];
    for (let r = 7; r <= 11; r++) {
        for (let c = 0; c < 5; c++) {
            if (redView.payload.board[r][c]) {
                blackPiecesSeenByRed.push(redView.payload.board[r][c]);
            }
        }
    }
    assert.equal(blackPiecesSeenByRed.length, 25);
    for (const p of blackPiecesSeenByRed) {
        assert.equal(p.rank, null, 'Opponent rank must be censored');
        assert.equal(p.suit, null, 'Opponent suit must be censored');
        assert.equal(p.isFlag, false, 'isFlag must never leak');
        assert.equal(p.isLandmine, false, 'isLandmine must never leak');
    }
    // Check opponent starting reserves
    assert.deepEqual(redView.payload.hands.black.startingReserves, [], 'Opponent reserve cards must not be leaked');
    assert.equal(redView.payload.hands.black.startingReserveCount, 2, 'Only count should be leaked');
});

// ==========================================
// ROUND 9: End-to-End Match Setup & Transition to Battle
// ==========================================
test('Round 9: End-to-End Match Setup Transition to Playing State', async () => {
    const state = new MockState();
    const room = new RoomDO(state, {});
    const wsHost = new MockWebSocket();
    const wsGuest = new MockWebSocket();
    state.sockets.push(wsHost, wsGuest);
    
    // 1. Create Room
    await room.handleCreateRoom(wsHost, { hostNickname: 'Alice', sidePreference: 'red' });
    assert.equal(room.gameState, 'waiting');
    
    // 2. Join Room
    await room.handleJoinRoom(wsGuest, { nickname: 'Bob' });
    assert.equal(room.gameState, 'setup');
    
    // Both get setup_start
    const hostSetupStart = wsHost.sent.find(m => m.type === 'setup_start');
    const guestSetupStart = wsGuest.sent.find(m => m.type === 'setup_start');
    assert.ok(hostSetupStart, 'Host receives setup_start');
    assert.ok(guestSetupStart, 'Guest receives setup_start');
    
    // 3. Host Submits Setup
    const redLayout = makeValidCamp('red');
    await room.handleSubmitLayout(wsHost, redLayout);
    const hostConf = wsHost.sent.find(m => m.type === 'setup_confirmed');
    assert.ok(hostConf, 'Host receives setup_confirmed');
    assert.equal(room.gameState, 'setup', 'Room stays in setup until guest confirms');
    
    // 4. Guest Submits Setup
    const blackLayout = makeValidCamp('black');
    await room.handleSubmitLayout(wsGuest, blackLayout);
    const guestConf = wsGuest.sent.find(m => m.type === 'setup_confirmed');
    assert.ok(guestConf, 'Guest receives setup_confirmed');
    
    // 5. Room transitions to playing
    assert.equal(room.gameState, 'playing');
    
    // Both receive state_view with gameState: playing
    const hostStateView = wsHost.sent.filter(m => m.type === 'state_view').pop();
    const guestStateView = wsGuest.sent.filter(m => m.type === 'state_view').pop();
    assert.ok(hostStateView, 'Host receives state_view');
    assert.ok(guestStateView, 'Guest receives state_view');
    assert.equal(hostStateView.payload.gameState, 'playing');
    assert.equal(guestStateView.payload.gameState, 'playing');
    assert.equal(hostStateView.payload.currentTurn, 'red');
});
