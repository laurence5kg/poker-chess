/**
 * RoomDO: Durable Object Managing Authoritative 1v1 Matches
 * Runs the isomorphic GameEngine from game.js with zero client trust.
 */

import { GameEngine, Card, OFFICER_RANKS } from '../game.js';

export class RoomDO {
    constructor(state, env) {
        this.state = state;
        this.env = env;

        this.roomId = null;
        this.gameState = 'waiting'; // 'waiting' -> 'setup' -> 'playing' -> 'finished'
        this.hostRole = null; // 'red' | 'black' | 'random'
        this.currentTurn = 'red';
        this.winner = null;
        this.winReason = '';

        this.players = {
            red: null,   // { nickname, sessionToken, ws, connected, setupComplete }
            black: null
        };

        this.engine = new GameEngine();
        this.engine.mode = 'pvp';

        this.turnTimerSec = 60;
        this.disconnectGraceSec = 60;
        this.turnDeadline = 0;
        this.disconnectTimer = null;

        // Auto-hydrate state if evicted
        this.state.blockConcurrencyWhile(async () => {
            const saved = await this.state.storage.get('room_state');
            if (saved) {
                this.deserializeState(saved);
            }
        });
    }

    async fetch(request) {
        const url = new URL(request.url);

        if (request.headers.get('Upgrade')?.toLowerCase() === 'websocket') {
            const pair = new WebSocketPair();
            const [client, server] = Object.values(pair);

            if (this.state.acceptWebSocket) {
                this.state.acceptWebSocket(server);
            } else {
                server.accept();
            }

            // Route messages from this WebSocket
            this.setupWebSocketListeners(server);

            return new Response(null, { status: 101, webSocket: client });
        }

        // Direct state query for testing / inspection
        if (request.method === 'GET' && url.pathname.endsWith('/status')) {
            return new Response(JSON.stringify({
                roomId: this.roomId,
                gameState: this.gameState,
                currentTurn: this.currentTurn,
                players: {
                    red: this.players.red ? { nickname: this.players.red.nickname, connected: this.players.red.connected } : null,
                    black: this.players.black ? { nickname: this.players.black.nickname, connected: this.players.black.connected } : null
                }
            }), { headers: { 'Content-Type': 'application/json' } });
        }

        return new Response('Not Found', { status: 404 });
    }

    // Cloudflare WebSocket Hibernation API handlers
    async webSocketMessage(ws, message) {
        try {
            if (typeof message === 'string' && message.length > 4096) {
                ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'PAYLOAD_TOO_LARGE' } }));
                return;
            }
            const msg = JSON.parse(message);
            await this.handleClientMessage(ws, msg);
        } catch (err) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'MALFORMED_MESSAGE', message: err.message } }));
        }
    }

    async webSocketClose(ws, code, reason, wasClean) {
        this.handlePlayerDisconnect(ws);
    }

    setupWebSocketListeners(ws) {
        ws.addEventListener('message', async (event) => {
            await this.webSocketMessage(ws, event.data);
        });

        ws.addEventListener('close', () => {
            this.handlePlayerDisconnect(ws);
        });
    }

    async handleClientMessage(ws, msg) {
        if (!msg || typeof msg !== 'object') return;

        // Version check
        if (msg.v !== 1) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'VERSION_MISMATCH', pleaseRefresh: true } }));
            return;
        }

        switch (msg.type) {
            case 'create_room':
                return this.handleCreateRoom(ws, msg.payload);
            case 'join_room':
                return this.handleJoinRoom(ws, msg.payload);
            case 'submit_layout':
                return this.handleSubmitLayout(ws, msg.payload);
            case 'action':
                return this.handlePlayerAction(ws, msg.payload);
            case 'forfeit':
                return this.handleForfeit(ws);
            case 'reconnect':
                return this.handleReconnect(ws, msg.payload);
            default:
                ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'UNKNOWN_MESSAGE_TYPE' } }));
        }
    }

    // --- Matchmaking & Setup ---

    generateSessionToken() {
        return Array.from(crypto.getRandomValues(new Uint8Array(16)))
            .map(b => b.toString(16).padStart(2, '0')).join('');
    }

    sanitizeNickname(name) {
        if (!name || typeof name !== 'string') return 'Player';
        const cleaned = name.trim().replace(/[^a-zA-Z0-9_\u4e00-\u9fa5 -]/g, '').slice(0, 16);
        return cleaned || 'Player';
    }

    async handleCreateRoom(ws, payload = {}) {
        if (this.gameState !== 'waiting' || this.players.red || this.players.black) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'ROOM_ALREADY_INITIALIZED' } }));
            return;
        }

        this.roomId = payload.roomId || `room_${Date.now()}`;
        this.hostRole = payload.sidePreference || 'random';
        const hostNickname = this.sanitizeNickname(payload.hostNickname);
        const token = this.generateSessionToken();

        // Tentatively assign side if explicit, or wait for guest if random
        let assignedSide = 'red';
        if (this.hostRole === 'black') assignedSide = 'black';
        else if (this.hostRole === 'random') assignedSide = Math.random() < 0.5 ? 'red' : 'black';

        this.players[assignedSide] = {
            role: 'host',
            nickname: hostNickname,
            sessionToken: token,
            ws,
            connected: true,
            setupComplete: false,
            setupData: null
        };

        ws.send(JSON.stringify({
            v: 1,
            type: 'room_joined',
            payload: {
                roomId: this.roomId,
                role: 'host',
                playerColor: assignedSide,
                sessionToken: token
            }
        }));

        await this.registerWithLobby(hostNickname, this.hostRole);
        await this.persistState();
    }

    async registerWithLobby(hostNickname, sidePreference) {
        if (!this.env || !this.env.LOBBY_DO) return;
        try {
            const lobbyId = this.env.LOBBY_DO.idFromName('global-lobby');
            const lobbyStub = this.env.LOBBY_DO.get(lobbyId);
            await lobbyStub.fetch('http://internal/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    roomId: this.roomId,
                    hostNickname,
                    sidePreference
                })
            });
        } catch (err) {
            console.warn('Failed to register room with lobby:', err.message);
        }
    }

    async unregisterFromLobby() {
        if (!this.env || !this.env.LOBBY_DO) return;
        try {
            const lobbyId = this.env.LOBBY_DO.idFromName('global-lobby');
            const lobbyStub = this.env.LOBBY_DO.get(lobbyId);
            await lobbyStub.fetch('http://internal/unregister', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ roomId: this.roomId })
            });
        } catch (err) {
            console.warn('Failed to unregister room from lobby:', err.message);
        }
    }

    async handleJoinRoom(ws, payload = {}) {
        if (this.gameState !== 'waiting') {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'ROOM_NOT_JOINABLE' } }));
            return;
        }

        const guestNickname = this.sanitizeNickname(payload.nickname);
        const token = this.generateSessionToken();

        const hostColor = this.players.red ? 'red' : 'black';
        const guestColor = hostColor === 'red' ? 'black' : 'red';

        this.players[guestColor] = {
            role: 'guest',
            nickname: guestNickname,
            sessionToken: token,
            ws,
            connected: true,
            setupComplete: false,
            setupData: null
        };

        ws.send(JSON.stringify({
            v: 1,
            type: 'room_joined',
            payload: {
                roomId: this.roomId,
                role: 'guest',
                playerColor: guestColor,
                sessionToken: token
            }
        }));

        // Transition room to 'setup' phase
        this.gameState = 'setup';
        await this.unregisterFromLobby();

        // Notify both players to begin secret deployment
        for (const [color, p] of Object.entries(this.players)) {
            const oppColor = color === 'red' ? 'black' : 'red';
            const oppName = this.players[oppColor].nickname;
            this.sendToPlayer(color, {
                type: 'setup_start',
                payload: {
                    playerColor: color,
                    opponentNickname: oppName,
                    setupTimeLimitMs: 120000
                }
            });
        }

        await this.persistState();
    }

    async handleSubmitLayout(ws, payload) {
        if (this.gameState !== 'setup') {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'NOT_IN_SETUP_PHASE' } }));
            return;
        }

        const playerColor = this.getPlayerColorByWs(ws);
        if (!playerColor) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'UNAUTHORIZED' } }));
            return;
        }

        const { camp, reserves } = payload;
        if (!Array.isArray(camp) || camp.length !== 25 || !Array.isArray(reserves) || reserves.length !== 2) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'INVALID_LAYOUT_COUNTS' } }));
            return;
        }

        // Validate deployment on temporary sub-engine
        const testEngine = new GameEngine();
        testEngine.initSetup(playerColor);

        for (const piece of camp) {
            const card = new Card(playerColor, piece.suit, piece.rank, piece.rank === 'JOKER');
            testEngine.board[piece.r][piece.c] = card;
        }
        testEngine.hands[playerColor].startingReserves = reserves.map(r =>
            new Card(playerColor, r.suit, r.rank, r.rank === 'JOKER')
        );

        const val = testEngine.validateSetup(playerColor);
        if (!val.valid) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'INVALID_SETUP_RULES', errors: val.errors } }));
            return;
        }

        // Store validated layout
        this.players[playerColor].setupData = { camp, reserves };
        this.players[playerColor].setupComplete = true;

        ws.send(JSON.stringify({ v: 1, type: 'setup_confirmed', payload: { playerColor } }));

        // If both players have completed setup, launch battle!
        if (this.players.red.setupComplete && this.players.black.setupComplete) {
            await this.startBattle();
        } else {
            await this.persistState();
        }
    }

    async startBattle() {
        this.gameState = 'playing';
        this.currentTurn = 'red'; // Red moves first

        // Populate authoritative engine
        this.engine = new GameEngine();
        this.engine.mode = 'pvp';
        this.engine.gameState = 'playing';
        this.engine.currentTurn = 'red';

        for (const color of ['red', 'black']) {
            const layout = this.players[color].setupData;
            for (const piece of layout.camp) {
                const card = new Card(color, piece.suit, piece.rank, piece.rank === 'JOKER');
                this.engine.board[piece.r][piece.c] = card;
            }
            this.engine.hands[color].startingReserves = layout.reserves.map(r =>
                new Card(color, r.suit, r.rank, r.rank === 'JOKER')
            );
        }

        this.resetTurnTimer();
        this.broadcastStateViews();
        await this.persistState();
    }

    // --- Playing Phase & Legal Action Verification ---

    async handlePlayerAction(ws, payload) {
        if (this.gameState !== 'playing') {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'NOT_IN_PLAYING_STATE' } }));
            return;
        }

        const playerColor = this.getPlayerColorByWs(ws);
        if (!playerColor || playerColor !== this.currentTurn) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'NOT_YOUR_TURN' } }));
            return;
        }

        const legalActions = this.engine.getAllLegalActions(this.currentTurn);
        let matchedAction = null;

        if (payload.type === 'move') {
            matchedAction = legalActions.find(a =>
                a.type === 'move' &&
                a.from.r === payload.from?.r && a.from.c === payload.from?.c &&
                a.to.r === payload.to?.r && a.to.c === payload.to?.c
            );
        } else if (payload.type === 'drop') {
            matchedAction = legalActions.find(a =>
                a.type === 'drop' &&
                a.handType === payload.handType &&
                a.index === payload.index &&
                a.to.r === payload.to?.r && a.to.c === payload.to?.c
            );
        }

        if (!matchedAction) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'ILLEGAL_ACTION' } }));
            return;
        }

        // Execute authoritative action
        let actionResult = null;
        if (matchedAction.type === 'move') {
            this.engine.movePiece(matchedAction.from.r, matchedAction.from.c, matchedAction.to.r, matchedAction.to.c);
        } else if (matchedAction.type === 'drop') {
            this.engine.dropCard(matchedAction.handType, matchedAction.index, matchedAction.to.r, matchedAction.to.c);
        }

        actionResult = {
            action: { type: matchedAction.type, from: matchedAction.from, to: matchedAction.to, handType: matchedAction.handType, index: matchedAction.index },
            clash: this.engine.lastClashResult ? {
                attacker: this.sanitizeCardForClash(this.engine.lastClashResult.attacker),
                defender: this.sanitizeCardForClash(this.engine.lastClashResult.defender),
                winner: this.engine.lastClashResult.winner,
                outcomeText: this.engine.lastClashResult.outcomeText,
                sound: this.engine.lastClashResult.sound
            } : null
        };

        // Broadcast action result
        this.broadcast({
            v: 1,
            type: 'action_result',
            payload: actionResult
        });

        // Check game over
        if (this.engine.gameState === 'gameover') {
            this.gameState = 'finished';
            this.winner = this.engine.winner;
            this.winReason = this.engine.winReason;

            this.broadcast({
                v: 1,
                type: 'game_over',
                payload: {
                    winner: this.winner,
                    reason: this.winReason,
                    forfeitedBy: null
                }
            });
        } else {
            this.currentTurn = this.engine.currentTurn;
            this.resetTurnTimer();
        }

        this.broadcastStateViews();
        await this.persistState();
    }

    sanitizeCardForClash(card) {
        if (!card) return null;
        return {
            player: card.player,
            originalOwner: card.originalOwner,
            rank: card.rank,
            suit: card.suit,
            roleName: card.roleName,
            isFlag: card.isFlag,
            isBomb: card.isBomb,
            isLandmine: card.isLandmine,
            isSapper: card.isSapper,
            isMochigoma: card.isMochigoma
        };
    }

    resetTurnTimer() {
        this.turnDeadline = Date.now() + (this.turnTimerSec * 1000);
    }

    // --- View Projection: ZERO INFORMATION LEAKAGE ---

    projectStateView(forPlayer) {
        const opponentColor = forPlayer === 'red' ? 'black' : 'red';

        // 1. Board projection: Hide all face-down opponent pieces
        const projectedBoard = [];
        for (let r = 0; r < 12; r++) {
            const row = [];
            for (let c = 0; c < 5; c++) {
                const card = this.engine.board[r][c];
                if (!card) {
                    row.push(null);
                } else if (card.player === forPlayer) {
                    // Own piece: full information
                    row.push({
                        player: card.player,
                        originalOwner: card.originalOwner,
                        rank: card.rank,
                        suit: card.suit,
                        faceUp: true,
                        isFlag: card.isFlag,
                        isBomb: card.isBomb,
                        isLandmine: card.isLandmine,
                        isSapper: card.isSapper,
                        isMochigoma: card.isMochigoma
                    });
                } else {
                    // Opponent piece
                    if (card.faceUp) {
                        // Publicly revealed (e.g. Conscript Mochigoma drop)
                        row.push({
                            player: card.player,
                            originalOwner: card.originalOwner,
                            rank: card.rank,
                            suit: card.suit,
                            faceUp: true,
                            isFlag: card.isFlag,
                            isBomb: card.isBomb,
                            isLandmine: card.isLandmine,
                            isSapper: card.isSapper,
                            isMochigoma: card.isMochigoma
                        });
                    } else {
                        // STRICT FOG OF WAR: Strip all hidden properties!
                        row.push({
                            player: card.player,
                            originalOwner: card.originalOwner,
                            rank: null,
                            suit: null,
                            faceUp: false,
                            isFlag: false,
                            isBomb: false,
                            isLandmine: false,
                            isSapper: false,
                            isMochigoma: false
                        });
                    }
                }
            }
            projectedBoard.push(row);
        }

        // 2. Hands projection: Hide opponent reserve identities
        const myHands = this.engine.hands[forPlayer] || { startingReserves: [], mochigoma: [] };
        const oppHands = this.engine.hands[opponentColor] || { startingReserves: [], mochigoma: [] };

        const projectedHands = {
            [forPlayer]: {
                startingReserves: myHands.startingReserves.map(c => ({
                    rank: c.rank,
                    suit: c.suit,
                    isBomb: c.isBomb,
                    isLandmine: c.isLandmine,
                    isFlag: c.isFlag,
                    isSapper: c.isSapper
                })),
                mochigoma: myHands.mochigoma.map(c => ({
                    rank: c.rank,
                    suit: c.suit,
                    roleName: c.roleName
                }))
            },
            [opponentColor]: {
                startingReserveCount: oppHands.startingReserves.length,
                startingReserves: [], // STRIPPED: NO CARDS TRANSMITTED
                mochigoma: oppHands.mochigoma.map(c => ({
                    rank: c.rank,
                    suit: c.suit,
                    roleName: c.roleName
                }))
            }
        };

        // 3. Graveyard: Public to both players
        const projectedGraveyard = this.engine.graveyard.map(c => ({
            originalOwner: c.originalOwner,
            rank: c.rank,
            suit: c.suit,
            isFlag: c.isFlag,
            isBomb: c.isBomb,
            isLandmine: c.isLandmine,
            isSapper: c.isSapper,
            isMochigoma: c.isMochigoma
        }));

        return {
            v: 1,
            type: 'state_view',
            payload: {
                gameState: this.gameState,
                currentTurn: this.currentTurn,
                yourSide: forPlayer,
                turnTimerRemainingMs: Math.max(0, this.turnDeadline - Date.now()),
                board: projectedBoard,
                hands: projectedHands,
                graveyard: projectedGraveyard,
                legalActions: (this.gameState === 'playing' && this.currentTurn === forPlayer) ?
                    this.engine.getAllLegalActions(forPlayer).map(a => ({
                        type: a.type,
                        from: a.from,
                        to: a.to,
                        handType: a.handType,
                        index: a.index
                    })) : []
            }
        };
    }

    broadcastStateViews() {
        for (const side of ['red', 'black']) {
            if (this.players[side]?.ws && this.players[side]?.connected) {
                const view = this.projectStateView(side);
                this.sendToPlayer(side, view);
            }
        }
    }

    // --- Reconnect & Disconnect Management ---

    async handleReconnect(ws, payload = {}) {
        const { sessionToken } = payload;
        if (!sessionToken) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'INVALID_TOKEN' } }));
            return;
        }

        const color = Object.keys(this.players).find(c => this.players[c]?.sessionToken === sessionToken);
        if (!color) {
            ws.send(JSON.stringify({ v: 1, type: 'error', payload: { code: 'SESSION_NOT_FOUND' } }));
            return;
        }

        // Reconnect player
        this.players[color].ws = ws;
        this.players[color].connected = true;

        if (this.disconnectTimer) {
            clearTimeout(this.disconnectTimer);
            this.disconnectTimer = null;
        }

        ws.send(JSON.stringify({
            v: 1,
            type: 'room_joined',
            payload: {
                roomId: this.roomId,
                role: this.players[color].role,
                playerColor: color,
                sessionToken
            }
        }));

        // Notify opponent that player has returned
        const oppColor = color === 'red' ? 'black' : 'red';
        this.sendToPlayer(oppColor, {
            type: 'opponent_status',
            payload: { connected: true, gracePeriodRemainingMs: 0 }
        });

        // Stream immediate projected state
        if (this.gameState === 'playing') {
            ws.send(JSON.stringify(this.projectStateView(color)));
        } else if (this.gameState === 'setup') {
            ws.send(JSON.stringify({
                v: 1,
                type: 'setup_start',
                payload: {
                    playerColor: color,
                    opponentNickname: this.players[oppColor]?.nickname || 'Opponent',
                    setupTimeLimitMs: 120000
                }
            }));
        }

        await this.persistState();
    }

    handlePlayerDisconnect(ws) {
        const color = this.getPlayerColorByWs(ws);
        if (!color || !this.players[color]) return;

        this.players[color].connected = false;
        this.players[color].ws = null;

        if (this.gameState === 'playing' || this.gameState === 'setup') {
            const oppColor = color === 'red' ? 'black' : 'red';
            this.sendToPlayer(oppColor, {
                type: 'opponent_status',
                payload: {
                    connected: false,
                    gracePeriodRemainingMs: this.disconnectGraceSec * 1000
                }
            });

            // Start 60s disconnect grace timer
            if (!this.disconnectTimer) {
                this.disconnectTimer = setTimeout(() => {
                    this.handleAbandonment(color);
                }, this.disconnectGraceSec * 1000);
            }
        }
    }

    handleAbandonment(abandonedColor) {
        if (this.gameState === 'finished') return;
        const winner = abandonedColor === 'red' ? 'black' : 'red';
        this.gameState = 'finished';
        this.winner = winner;
        this.winReason = `Opponent disconnected (Grace period expired)`;

        this.broadcast({
            v: 1,
            type: 'game_over',
            payload: {
                winner: this.winner,
                reason: this.winReason,
                forfeitedBy: abandonedColor
            }
        });
    }

    async handleForfeit(ws) {
        const color = this.getPlayerColorByWs(ws);
        if (!color || this.gameState !== 'playing') return;

        const winner = color === 'red' ? 'black' : 'red';
        this.gameState = 'finished';
        this.winner = winner;
        this.winReason = `${color.toUpperCase()} surrendered`;

        this.broadcast({
            v: 1,
            type: 'game_over',
            payload: {
                winner: this.winner,
                reason: this.winReason,
                forfeitedBy: color
            }
        });

        await this.persistState();
    }

    // --- Helpers & Utilities ---

    getPlayerColorByWs(ws) {
        if (this.players.red?.ws === ws) return 'red';
        if (this.players.black?.ws === ws) return 'black';
        return null;
    }

    sendToPlayer(color, msgObj) {
        const player = this.players[color];
        if (player?.ws && player?.connected) {
            try {
                const json = JSON.stringify(msgObj.v ? msgObj : { v: 1, ...msgObj });
                player.ws.send(json);
            } catch (err) {
                // Connection lost
            }
        }
    }

    broadcast(msgObj) {
        const json = JSON.stringify(msgObj.v ? msgObj : { v: 1, ...msgObj });
        for (const side of ['red', 'black']) {
            if (this.players[side]?.ws && this.players[side]?.connected) {
                try {
                    this.players[side].ws.send(json);
                } catch (e) {}
            }
        }
    }

    async persistState() {
        if (!this.state.storage) return;
        try {
            await this.state.storage.put('room_state', this.serializeState());
        } catch (e) {
            // Memory-only fallback during unit testing
        }
    }

    serializeState() {
        return {
            roomId: this.roomId,
            gameState: this.gameState,
            hostRole: this.hostRole,
            currentTurn: this.currentTurn,
            winner: this.winner,
            winReason: this.winReason,
            players: {
                red: this.players.red ? {
                    nickname: this.players.red.nickname,
                    sessionToken: this.players.red.sessionToken,
                    role: this.players.red.role,
                    setupComplete: this.players.red.setupComplete,
                    setupData: this.players.red.setupData
                } : null,
                black: this.players.black ? {
                    nickname: this.players.black.nickname,
                    sessionToken: this.players.black.sessionToken,
                    role: this.players.black.role,
                    setupComplete: this.players.black.setupComplete,
                    setupData: this.players.black.setupData
                } : null
            }
        };
    }

    deserializeState(data) {
        if (!data) return;
        this.roomId = data.roomId;
        this.gameState = data.gameState;
        this.hostRole = data.hostRole;
        this.currentTurn = data.currentTurn;
        this.winner = data.winner;
        this.winReason = data.winReason;
        if (data.players) {
            for (const color of ['red', 'black']) {
                if (data.players[color]) {
                    this.players[color] = {
                        ...data.players[color],
                        ws: null,
                        connected: false
                    };
                }
            }
        }
    }
}
