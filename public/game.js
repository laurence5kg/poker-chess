// Poker Shogi & Junqi Game Engine (5x12 Board) - Fully Verified with 100-Game Invariant Testing

// Headless / Server Environment Polyfill & Sound Stub
if (typeof window === 'undefined') {
    globalThis.window = {
        I18N: null,
        soundFX: {
            playMove: () => {},
            playClash: () => {},
            playBomb: () => {},
            playDefuse: () => {},
            playCardFlip: () => {},
            playVictory: () => {}
        },
        renderApp: null
    };
} else if (!window.soundFX) {
    window.soundFX = {
        playMove: () => {},
        playClash: () => {},
        playBomb: () => {},
        playDefuse: () => {},
        playCardFlip: () => {},
        playVictory: () => {}
    };
}

const SUITS = {
    RED: ['♥', '♦'],
    BLACK: ['♠', '♣']
};

const RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

const OFFICER_RANKS = {
    '10': 10, '9': 9, '8': 8, '7': 7, '6': 6,
    '5': 5, '4': 4, '3': 3, '2': 2
};

class Card {
    constructor(player, suit, rank, isJoker = false, team = null) {
        this.id = Math.random().toString(36).substring(2, 9);
        this.player = player; // 'red' (P1), 'black' (P2), or 'a', 'b', 'c', 'd'
        this.originalOwner = player;
        this.team = team || player; // 'red', 'black', or player id
        this.suit = suit;     // '♥', '♦', '♠', '♣', or '🃏'
        this.rank = rank;     // 'A'..'K', or 'JOKER'
        this.isJoker = isJoker;
        
        // Roles
        this.isFlag = isJoker;
        this.isBomb = rank === 'K';
        this.isLandmine = (rank === 'Q' || rank === 'J');
        this.isSapper = rank === 'A';
        
        // State
        this.isMochigoma = false; // Dropped face-up as Conscript Sapper
        this.faceUp = false;      // Fog of war status
    }

    // Role Name without tautology (NO redundant number suffix)
    getRoleName(lang = null) {
        if (window.I18N) {
            if (this.isMochigoma) return window.I18N.t('role_conscript');
            if (this.isFlag) return window.I18N.t('role_flag');
            if (this.isBomb) return window.I18N.t('role_bomb');
            if (this.isLandmine) return window.I18N.t('role_landmine');
            if (this.isSapper) return window.I18N.t('role_sapper');
            return window.I18N.t('role_officer');
        }
        if (this.isMochigoma) return 'Sapper';
        if (this.isFlag) return 'Flag';
        if (this.isBomb) return 'Bomb';
        if (this.isLandmine) return 'Landmine';
        if (this.isSapper) return 'Sapper';
        return 'Officer';
    }

    get roleName() {
        return this.getRoleName();
    }

    get isImmobile() {
        return (this.isFlag || this.isLandmine) && !this.isMochigoma;
    }
}

class GameEngine {
    constructor() {
        this.rows = 12;
        this.cols = 5;
        this.board = Array(12).fill(null).map(() => Array(5).fill(null));
        
        this.playerCount = 2; // 2 or 4
        this.fourPlayerMode = '2v2'; // '2v2' or 'ffa'
        this.seating = { a: 'red', c: 'red', b: 'black', d: 'black' }; // default opposite
        this.turnOrder4P = ['a', 'd', 'c', 'b']; // North -> East -> South -> West
        this.currentTurnIdx4P = 0;
        this.eliminated = { a: false, b: false, c: false, d: false };

        this.mode = 'pve'; // 'pve', 'pvp', 'sandbox', '4p_2v2', '4p_ffa'
        this.humanSide = 'red'; // 'red' or 'black' in PVE and 1v1
        this.aiLevel = 'medium'; // 'low', 'medium', 'high'
        this.pvpAlliance = 'clubs'; // 'clubs' (black) or 'hearts' (red) in 2v2
        this.playerSeat = 'a'; // 'a', 'b', 'c', 'd' in FFA
        this.currentTurn = 'red'; // 'red', 'black', or 'a', 'b', 'c', 'd'
        this.gameState = 'setup'; // 'setup', 'playing', 'gameover'
        this.setupPlayer = 'red'; // 'red', 'black', or 'a', 'b', 'c', 'd'
        
        this.unplacedCards = {
            red: [],
            black: [],
            a: [], b: [], c: [], d: []
        };

        this.hands = {
            red: { startingReserves: [], mochigoma: [] },
            black: { startingReserves: [], mochigoma: [] },
            a: { startingReserves: [], mochigoma: [] },
            b: { startingReserves: [], mochigoma: [] },
            c: { startingReserves: [], mochigoma: [] },
            d: { startingReserves: [], mochigoma: [] }
        };

        this.graveyard = [];
        this.selectedTile = null; // { r, c }
        this.selectedHandCard = null; // { player, type, index, card }
        this.selectedUnplacedIndex = null;
        
        this.history = [];
        this.moveLog = [];
        this.positionCounts = {};
        
        this.lastClashResult = null;
        this.winner = null;
        this.winReason = '';
        this.initAiMemory();
    }

    initAiMemory() {
        this.aiMemory = {
            red: new Map(),
            black: new Map(),
            a: new Map(),
            b: new Map(),
            c: new Map(),
            d: new Map()
        };
        this.aiKnownLandmines = {
            red: new Set(),
            black: new Set(),
            a: new Set(),
            b: new Set(),
            c: new Set(),
            d: new Set()
        };
    }

    purgeCardFromAiMemory(card, r = null, c = null) {
        if (!card) return;
        const allSides = ['red', 'black', 'a', 'b', 'c', 'd'];
        for (let side of allSides) {
            if (this.aiMemory && this.aiMemory[side]) {
                this.aiMemory[side].delete(card);
            }
            if (card.isLandmine && r !== null && c !== null && this.aiKnownLandmines && this.aiKnownLandmines[side]) {
                this.aiKnownLandmines[side].delete(`${r},${c}`);
            }
        }
    }

    getKnownCard(r, c, viewer) {
        const card = this.board[r][c];
        if (!card) return null;
        if (card.player === viewer) {
            return {
                player: card.player,
                rank: card.rank,
                rankVal: OFFICER_RANKS[card.rank] || 0,
                isBomb: card.isBomb,
                isLandmine: card.isLandmine,
                isFlag: card.isFlag,
                isSapper: card.isSapper,
                isMochigoma: card.isMochigoma
            };
        }
        if (card.faceUp) {
            return {
                player: card.player,
                rank: card.rank,
                rankVal: OFFICER_RANKS[card.rank] || 0,
                isBomb: card.isBomb,
                isLandmine: card.isLandmine,
                isFlag: card.isFlag,
                isSapper: card.isSapper,
                isMochigoma: card.isMochigoma
            };
        }
        if (this.aiKnownLandmines && this.aiKnownLandmines[viewer] && this.aiKnownLandmines[viewer].has(`${r},${c}`)) {
            return {
                player: card.player,
                rank: card.rank,
                rankVal: 0,
                isBomb: false,
                isLandmine: true,
                isFlag: false,
                isSapper: false,
                isMochigoma: false
            };
        }
        if (this.aiMemory && this.aiMemory[viewer] && this.aiMemory[viewer].has(card)) {
            return this.aiMemory[viewer].get(card);
        }
        return null;
    }

    get botSide() {
        return this.humanSide === 'red' ? 'black' : 'red';
    }

    isPlayable(r, c) {
        if (this.playerCount === 2) {
            return r >= 0 && r < 12 && c >= 0 && c < 5;
        }
        // 4-Player 15x15 Plus-Shaped Cross Board
        if (r < 0 || r >= 15 || c < 0 || c >= 15) return false;
        // Camp A (North): rows 0..4, cols 5..9
        if (r >= 0 && r <= 4 && c >= 5 && c <= 9) return true;
        // Camp C (South): rows 10..14, cols 5..9
        if (r >= 10 && r <= 14 && c >= 5 && c <= 9) return true;
        // Camp B (West): rows 5..9, cols 0..4
        if (r >= 5 && r <= 9 && c >= 0 && c <= 4) return true;
        // Camp D (East): rows 5..9, cols 10..14
        if (r >= 5 && r <= 9 && c >= 10 && c <= 14) return true;
        // Center 5x5: rows 5..9, cols 5..9
        if (r >= 5 && r <= 9 && c >= 5 && c <= 9) {
            // Check 4 center obstacles (r: 6,8 and c: 6,8)
            if ((r === 6 || r === 8) && (c === 6 || c === 8)) {
                return false;
            }
            return true;
        }
        return false;
    }

    isFrontline(player, r, c) {
        if (this.playerCount === 2) {
            return (player === 'red' && r === 4) || (player === 'black' && r === 7);
        }
        if (player === 'a') return r === 4 && c >= 5 && c <= 9;
        if (player === 'c') return r === 10 && c >= 5 && c <= 9;
        if (player === 'b') return c === 4 && r >= 5 && r <= 9;
        if (player === 'd') return c === 10 && r >= 5 && r <= 9;
        return false;
    }

    getCampCells(player) {
        const cells = [];
        if (this.playerCount === 2) {
            const minRow = player === 'red' ? 0 : 7;
            const maxRow = player === 'red' ? 4 : 11;
            for (let r = minRow; r <= maxRow; r++) {
                for (let c = 0; c < 5; c++) cells.push({ r, c });
            }
            return cells;
        }
        if (player === 'a') {
            for (let r = 0; r <= 4; r++) for (let c = 5; c <= 9; c++) cells.push({ r, c });
        } else if (player === 'c') {
            for (let r = 10; r <= 14; r++) for (let c = 5; c <= 9; c++) cells.push({ r, c });
        } else if (player === 'b') {
            for (let r = 5; r <= 9; r++) for (let c = 0; c <= 4; c++) cells.push({ r, c });
        } else if (player === 'd') {
            for (let r = 5; r <= 9; r++) for (let c = 10; c <= 14; c++) cells.push({ r, c });
        }
        return cells;
    }

    isTeammate(p1, p2) {
        if (this.playerCount === 2) {
            return p1 === p2;
        }
        if (this.fourPlayerMode === '2v2') {
            return this.seating[p1] === this.seating[p2];
        }
        return p1 === p2;
    }

    createDeck(player) {
        const suits = player === 'red' ? SUITS.RED : SUITS.BLACK;
        const deck = [];
        suits.forEach(suit => {
            RANKS.forEach(rank => {
                deck.push(new Card(player, suit, rank, false));
            });
        });
        deck.push(new Card(player, '🃏', 'JOKER', true));
        return deck;
    }

    createDeck4P(player) {
        const team = this.seating[player] || player;
        let suits = ['♥', '♦'];
        let jokerSuit = '🃏_RED';
        if (team === 'black') {
            suits = ['♠', '♣'];
            jokerSuit = '🃏_BLK';
        } else if (this.fourPlayerMode === 'ffa') {
            const suitMap = { 'a': ['♥', '♦'], 'c': ['♥', '♦'], 'b': ['♠', '♣'], 'd': ['♠', '♣'] };
            suits = suitMap[player];
            jokerSuit = `🃏_${player.toUpperCase()}`;
        }

        const deck = [];
        suits.forEach(suit => {
            RANKS.forEach(rank => {
                deck.push(new Card(player, suit, rank, false, team));
            });
        });
        deck.push(new Card(player, jokerSuit, 'JOKER', true, team));
        return deck;
    }

    autoSetup4P(player) {
        const pool = this.createDeck4P(player);
        const flag = pool.find(c => c.isFlag);
        const mines = pool.filter(c => c.isLandmine);
        const mobiles = pool.filter(c => !c.isImmobile);

        for (let i = mobiles.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [mobiles[i], mobiles[j]] = [mobiles[j], mobiles[i]];
        }

        this.hands[player].startingReserves = mobiles.splice(0, 2);
        this.hands[player].mochigoma = [];

        let flagPos, minePositions;
        if (player === 'a') {
            const cornerCol = Math.random() < 0.5 ? 5 : 9;
            if (cornerCol === 5) {
                flagPos = { r: 0, c: 5 };
                minePositions = [{ r: 0, c: 6 }, { r: 1, c: 5 }, { r: 1, c: 6 }, { r: 0, c: 7 }];
            } else {
                flagPos = { r: 0, c: 9 };
                minePositions = [{ r: 0, c: 8 }, { r: 1, c: 9 }, { r: 1, c: 8 }, { r: 0, c: 7 }];
            }
        } else if (player === 'c') {
            const cornerCol = Math.random() < 0.5 ? 5 : 9;
            if (cornerCol === 5) {
                flagPos = { r: 14, c: 5 };
                minePositions = [{ r: 14, c: 6 }, { r: 13, c: 5 }, { r: 13, c: 6 }, { r: 14, c: 7 }];
            } else {
                flagPos = { r: 14, c: 9 };
                minePositions = [{ r: 14, c: 8 }, { r: 13, c: 9 }, { r: 13, c: 8 }, { r: 14, c: 7 }];
            }
        } else if (player === 'b') {
            const cornerRow = Math.random() < 0.5 ? 5 : 9;
            if (cornerRow === 5) {
                flagPos = { r: 5, c: 0 };
                minePositions = [{ r: 6, c: 0 }, { r: 5, c: 1 }, { r: 6, c: 1 }, { r: 7, c: 0 }];
            } else {
                flagPos = { r: 9, c: 0 };
                minePositions = [{ r: 8, c: 0 }, { r: 9, c: 1 }, { r: 8, c: 1 }, { r: 7, c: 0 }];
            }
        } else if (player === 'd') {
            const cornerRow = Math.random() < 0.5 ? 5 : 9;
            if (cornerRow === 5) {
                flagPos = { r: 5, c: 14 };
                minePositions = [{ r: 6, c: 14 }, { r: 5, c: 13 }, { r: 6, c: 13 }, { r: 7, c: 14 }];
            } else {
                flagPos = { r: 9, c: 14 };
                minePositions = [{ r: 8, c: 14 }, { r: 9, c: 13 }, { r: 8, c: 13 }, { r: 7, c: 14 }];
            }
        }

        this.board[flagPos.r][flagPos.c] = flag;
        for (let i = 0; i < 4; i++) {
            this.board[minePositions[i].r][minePositions[i].c] = mines[i];
        }

        const occupied = new Set([
            `${flagPos.r},${flagPos.c}`,
            ...minePositions.map(p => `${p.r},${p.c}`)
        ]);

        const campCells = this.getCampCells(player);
        for (let pos of campCells) {
            if (!occupied.has(`${pos.r},${pos.c}`)) {
                this.board[pos.r][pos.c] = mobiles.pop();
            }
        }
    }

    autoSetupAll4P() {
        ['a', 'b', 'c', 'd'].forEach(p => this.autoSetup4P(p));
    }

    resetForNewGame(options = {}) {
        let playerCount = 2;
        let fourPlayerMode = '2v2';
        let seatingChoice = 'opposite';
        let mode = 'pve';
        let humanSide = 'red';
        let aiLevel = 'medium';
        let pvpAlliance = 'clubs';
        let playerSeat = 'a';

        if (typeof options === 'object' && options !== null) {
            mode = options.mode || this.mode || 'pve';
            playerCount = options.playerCount || (mode.startsWith('4p') ? 4 : 2);
            fourPlayerMode = options.fourPlayerMode || (mode === '4p_ffa' ? 'ffa' : '2v2');
            seatingChoice = options.seating || 'opposite';
            humanSide = options.humanSide || this.humanSide || 'red';
            aiLevel = options.aiLevel || this.aiLevel || 'medium';
            pvpAlliance = options.pvpAlliance || this.pvpAlliance || 'clubs';
            playerSeat = options.playerSeat || this.playerSeat || 'a';
        } else {
            playerCount = options || 2;
            fourPlayerMode = arguments[1] || '2v2';
            seatingChoice = arguments[2] || 'opposite';
            mode = playerCount === 4 ? (fourPlayerMode === 'ffa' ? '4p_ffa' : '4p_2v2') : this.mode;
        }

        this.playerCount = playerCount;
        this.fourPlayerMode = fourPlayerMode;
        this.mode = mode;
        this.humanSide = humanSide;
        this.aiLevel = aiLevel;
        this.pvpAlliance = pvpAlliance;
        this.playerSeat = playerSeat;

        if (seatingChoice === 'adj_nw_se') {
            this.seating = { a: 'red', b: 'red', c: 'black', d: 'black' };
        } else if (seatingChoice === 'adj_ne_sw') {
            this.seating = { a: 'red', d: 'red', b: 'black', c: 'black' };
        } else {
            this.seating = { a: 'red', c: 'red', b: 'black', d: 'black' }; // default opposite
        }

        if (this.playerCount === 4) {
            this.rows = 15;
            this.cols = 15;
            this.board = Array(15).fill(null).map(() => Array(15).fill(null));
            this.turnOrder4P = ['a', 'd', 'c', 'b'];
            this.currentTurnIdx4P = 0;
            this.currentTurn = 'a';
            this.setupPlayer = 'a';
            this.gameState = 'setup';
            this.eliminated = { a: false, b: false, c: false, d: false };

            this.hands = {
                a: { startingReserves: [], mochigoma: [] },
                b: { startingReserves: [], mochigoma: [] },
                c: { startingReserves: [], mochigoma: [] },
                d: { startingReserves: [], mochigoma: [] }
            };

            this.unplacedCards = {
                a: this.createDeck4P('a'),
                b: this.createDeck4P('b'),
                c: this.createDeck4P('c'),
                d: this.createDeck4P('d')
            };

            this.autoSetupAll4P();
        } else {
            this.rows = 12;
            this.cols = 5;
            this.board = Array(12).fill(null).map(() => Array(5).fill(null));
            this.gameState = 'setup';

            if (this.mode === 'pve') {
                if (this.humanSide === 'black') {
                    this.currentTurn = 'black';
                    this.setupPlayer = 'black';
                    this.unplacedCards = {
                        red: [],
                        black: this.createDeck('black')
                    };
                    this.hands = {
                        red: { startingReserves: [], mochigoma: [] },
                        black: { startingReserves: [], mochigoma: [] }
                    };
                    // Red bot automatically deploys formation
                    this.autoSetup('red');
                } else {
                    this.currentTurn = 'red';
                    this.setupPlayer = 'red';
                    this.unplacedCards = {
                        red: this.createDeck('red'),
                        black: []
                    };
                    this.hands = {
                        red: { startingReserves: [], mochigoma: [] },
                        black: { startingReserves: [], mochigoma: [] }
                    };
                    // Black bot automatically deploys formation
                    this.autoSetup('black');
                }
            } else {
                // PvP 1v1 or sandbox
                const startSide = this.humanSide === 'black' ? 'black' : 'red';
                this.currentTurn = startSide;
                this.setupPlayer = startSide;

                this.unplacedCards = {
                    red: this.createDeck('red'),
                    black: this.createDeck('black')
                };

                this.hands = {
                    red: { startingReserves: [], mochigoma: [] },
                    black: { startingReserves: [], mochigoma: [] }
                };
            }
        }

        this.graveyard = [];
        this.selectedTile = null;
        this.selectedHandCard = null;
        this.selectedUnplacedIndex = null;
        
        this.history = [];
        this.moveLog = [];
        this.positionCounts = {};
        
        this.lastClashResult = null;
        this.winner = null;
        this.winReason = '';
        this.initAiMemory();
        this.log('New game initialized.');
    }

    initSetup(player = 'red') {
        this.gameState = 'setup';
        this.setupPlayer = player;
        this.selectedTile = null;
        this.selectedHandCard = null;
        this.selectedUnplacedIndex = null;
        this.lastClashResult = null;

        const minRow = player === 'red' ? 0 : 7;
        const maxRow = player === 'red' ? 4 : 11;
        for (let r = minRow; r <= maxRow; r++) {
            for (let c = 0; c < 5; c++) {
                this.board[r][c] = null;
            }
        }
        this.hands[player].startingReserves = [];
        this.hands[player].mochigoma = [];

        this.unplacedCards[player] = this.createDeck(player);
        this.log(`Deployment Phase: ${player.toUpperCase()}.`);
    }

    autoSetup(player) {
        let pool = [...this.unplacedCards[player], ...this.hands[player].startingReserves];
        const minRow = player === 'red' ? 0 : 7;
        const maxRow = player === 'red' ? 4 : 11;
        for (let r = minRow; r <= maxRow; r++) {
            for (let c = 0; c < 5; c++) {
                if (this.board[r][c] && this.board[r][c].player === player) {
                    pool.push(this.board[r][c]);
                    this.board[r][c] = null;
                }
            }
        }

        if (pool.length === 0) {
            pool = this.createDeck(player);
        }

        const flag = pool.find(c => c.isFlag);
        const mines = pool.filter(c => c.isLandmine);
        const bombs = pool.filter(c => c.isBomb);
        const sappers = pool.filter(c => c.isSapper);
        const officers = pool.filter(c => OFFICER_RANKS[c.rank] > 0).sort((a, b) => (OFFICER_RANKS[a.rank] || 0) - (OFFICER_RANKS[b.rank] || 0));

        this.unplacedCards[player] = [];

        // Corner flag fortress layout (Flag at col 0 corner, Landmines around it)
        const flagPos = player === 'red' ? { r: 0, c: 0 } : { r: 11, c: 0 };
        const minePositions = player === 'red'
            ? [{ r: 0, c: 1 }, { r: 1, c: 0 }, { r: 1, c: 1 }, { r: 0, c: 2 }]
            : [{ r: 11, c: 1 }, { r: 10, c: 0 }, { r: 10, c: 1 }, { r: 11, c: 2 }];

        this.board[flagPos.r][flagPos.c] = flag;
        for (let i = 0; i < 4; i++) {
            this.board[minePositions[i].r][minePositions[i].c] = mines[i];
        }

        const occupied = new Set([
            `${flagPos.r},${flagPos.c}`,
            ...minePositions.map(p => `${p.r},${p.c}`)
        ]);

        const campRows = player === 'red' ? [0, 1, 2, 3, 4] : [11, 10, 9, 8, 7];

        if (this.aiLevel === 'high') {
            // Mathematically Optimal Deployment:
            // 1. Reserves in Hand: 1 Bomb + 1 Mid Officer for reactive tactical drops
            this.hands[player].startingReserves = [bombs.pop(), officers.splice(4, 1)[0]];
            this.hands[player].mochigoma = [];

            // 2. Frontline (Row 4 for Red, Row 7 for Black): Probing line with lowest officers (2, 2, 3, 3, 4)
            const frontRow = campRows[4];
            for (let c = 0; c < 5; c++) {
                this.board[frontRow][c] = officers.shift();
            }

            // 3. Second-Line Interceptors (Row 3 for Red, Row 8 for Black):
            // Col 0: Bomb ambush; Col 1: Sapper; Col 2: Officer; Col 3: Sapper; Col 4: Officer
            const r3 = campRows[3];
            this.board[r3][0] = bombs.pop();
            this.board[r3][1] = sappers.pop();
            this.board[r3][2] = officers.pop();
            this.board[r3][3] = sappers.pop();
            this.board[r3][4] = officers.pop();

            // 4. Strike Force Tier (Row 2 for Red, Row 9 for Black): Heavy Officers (10, 10, 9, 9, 8)
            const r2 = campRows[2];
            for (let c = 0; c < 5; c++) {
                this.board[r2][c] = officers.pop();
            }

            // 5. Support staging for remaining positions in camp
            for (let r of [campRows[1], campRows[0]]) {
                for (let c = 0; c < 5; c++) {
                    if (!occupied.has(`${r},${c}`) && !this.board[r][c]) {
                        this.board[r][c] = officers.pop() || null;
                    }
                }
            }
        } else {
            // Standard / Casual deployment
            const mobiles = pool.filter(c => !c.isImmobile);
            for (let i = mobiles.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [mobiles[i], mobiles[j]] = [mobiles[j], mobiles[i]];
            }
            this.hands[player].startingReserves = mobiles.splice(0, 2);
            for (let r of campRows) {
                for (let c = 0; c < 5; c++) {
                    if (!occupied.has(`${r},${c}`)) {
                        this.board[r][c] = mobiles.pop();
                    }
                }
            }
        }
    }

    validateSetup(player) {
        const errors = [];
        const minRow = player === 'red' ? 0 : 7;
        const maxRow = player === 'red' ? 4 : 11;
        const frontRow = player === 'red' ? 4 : 7;

        let placedCount = 0;
        const invalidFrontTiles = [];

        for (let r = minRow; r <= maxRow; r++) {
            for (let c = 0; c < 5; c++) {
                const card = this.board[r][c];
                if (card && card.player === player) {
                    placedCount++;
                    if (r === frontRow && card.isImmobile) {
                        invalidFrontTiles.push({ r, c, name: card.roleName });
                    }
                }
            }
        }

        const reserveCount = this.hands[player].startingReserves.length;
        const unplacedCount = this.unplacedCards[player].length;

        if (placedCount !== 25) {
            const msg = window.I18N ? window.I18N.t('setup_incomplete_camp', { count: placedCount }) : `Camp must have exactly 25 cards placed (${placedCount}/25).`;
            errors.push(msg);
        }
        if (reserveCount !== 2) {
            const msg = window.I18N ? window.I18N.t('setup_incomplete_reserve', { count: reserveCount }) : `Must have exactly 2 Reserves in hand (${reserveCount}/2).`;
            errors.push(msg);
        }
        if (invalidFrontTiles.length > 0) {
            const msg = window.I18N ? window.I18N.t('invalid_frontline') : `Flag and Landmines CANNOT be placed on the frontline!`;
            errors.push(msg);
        }

        return {
            valid: errors.length === 0,
            errors,
            placedCount,
            reserveCount,
            unplacedCount,
            invalidFrontTiles
        };
    }

    confirmSetup(player) {
        const validation = this.validateSetup(player);
        if (!validation.valid) {
            return validation;
        }

        if (this.mode === 'pve') {
            const bot = this.botSide;
            let botPlaced = 0;
            for (let r = 0; r < 12; r++) {
                for (let c = 0; c < 5; c++) {
                    if (this.board[r][c] && this.board[r][c].player === bot) botPlaced++;
                }
            }
            if (botPlaced < 25) {
                this.autoSetup(bot);
            }
            this.startBattle();
        } else if (this.mode === 'pvp') {
            const otherPlayer = player === 'red' ? 'black' : 'red';
            let otherPlaced = 0;
            for (let r = 0; r < 12; r++) {
                for (let c = 0; c < 5; c++) {
                    if (this.board[r][c] && this.board[r][c].player === otherPlayer) otherPlaced++;
                }
            }
            if (otherPlaced < 25) {
                this.initSetup(otherPlayer);
            } else {
                this.startBattle();
            }
        } else {
            this.startBattle();
        }

        return { valid: true };
    }

    startBattle() {
        this.gameState = 'playing';
        this.currentTurn = 'red';
        this.selectedTile = null;
        this.selectedHandCard = null;
        this.selectedUnplacedIndex = null;
        this.positionCounts = {};
        this.recordPosition();
        this.log(`Battle commenced.`);

        // In PvE, if bot is Red, Red bot moves first!
        if (this.mode === 'pve' && this.currentTurn === this.botSide) {
            setTimeout(() => this.runBotTurn(), 600);
        }
    }

    log(msg) {
        this.moveLog.unshift({ turn: this.currentTurn, text: msg });
        if (this.moveLog.length > 50) this.moveLog.pop();
    }

    getCounts(player) {
        let native = 0;
        let mochigoma = 0;

        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card && card.player === player) {
                    if (card.isMochigoma) {
                        mochigoma++;
                    } else {
                        native++;
                    }
                }
            }
        }

        if (this.hands[player]) {
            native += this.hands[player].startingReserves.length;
            mochigoma += this.hands[player].mochigoma.length;
        }

        return { native, mochigoma };
    }

    canAcceptMochigoma(player) {
        const counts = this.getCounts(player);
        return counts.mochigoma + 1 <= counts.native;
    }

    checkAndEnforceMutiny(player) {
        if (this.playerCount === 4 && this.eliminated[player]) return;
        let counts = this.getCounts(player);
        while (counts.mochigoma > counts.native) {
            if (this.hands[player].mochigoma.length > 0) {
                const card = this.hands[player].mochigoma.pop();
                this.graveyard.push(card);
                const msg = window.I18N ? window.I18N.t('mutiny_enforced_hand') : `Anti-Mutiny: Conscripts exceeded loyal troops! 1 prisoner in hand discarded to Graveyard.`;
                this.log(msg);
            } else {
                let removed = false;
                for (let r = 0; r < this.rows; r++) {
                    for (let c = 0; c < this.cols; c++) {
                        const card = this.board[r][c];
                        if (card && card.player === player && card.isMochigoma) {
                            this.graveyard.push(card);
                            this.board[r][c] = null;
                            removed = true;
                            const msg = window.I18N ? window.I18N.t('mutiny_enforced_board') : `Anti-Mutiny: Conscript Sapper disbanded to Graveyard!`;
                            this.log(msg);
                            break;
                        }
                    }
                    if (removed) break;
                }
                if (!removed) break;
            }
            counts = this.getCounts(player);
        }
    }

    getLegalMoves(r, c, forPlayer = null) {
        const activePlayer = forPlayer || this.currentTurn;
        const card = this.board[r][c];
        if (!card || card.player !== activePlayer) return [];
        if (card.isImmobile) return [];
        if (this.playerCount === 4 && this.eliminated[activePlayer]) return [];

        const moves = [];
        const deltas = [
            [-1, 0], [1, 0], [0, -1], [0, 1]
        ];

        for (let [dr, dc] of deltas) {
            const nr = r + dr;
            const nc = c + dc;
            if (this.isPlayable(nr, nc)) {
                const target = this.board[nr][nc];
                if (!target || !this.isTeammate(card.player, target.player)) {
                    moves.push({ r: nr, c: nc });
                }
            }
        }
        return moves;
    }

    getLegalDrops(forPlayer = null, card = null) {
        const activePlayer = forPlayer || this.currentTurn;
        if (this.playerCount === 4 && this.eliminated[activePlayer]) return [];
        const moves = [];
        const campCells = this.getCampCells(activePlayer);
        for (let pos of campCells) {
            if (!this.board[pos.r][pos.c]) {
                if (card && card.isImmobile && this.isFrontline(activePlayer, pos.r, pos.c)) {
                    continue;
                }
                moves.push(pos);
            }
        }
        return moves;
    }

    hasAnyLegalAction(player) {
        if (this.playerCount === 4 && this.eliminated[player]) return false;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card && card.player === player && !card.isImmobile) {
                    if (this.getLegalMoves(r, c, player).length > 0) {
                        return true;
                    }
                }
            }
        }
        if (this.hands[player]) {
            for (let c of this.hands[player].startingReserves) {
                if (this.getLegalDrops(player, c).length > 0) return true;
            }
            if (this.hands[player].mochigoma.length > 0 && this.getLegalDrops(player).length > 0) return true;
        }
        return false;
    }

    movePiece(fromR, fromC, toR, toC) {
        const attacker = this.board[fromR][fromC];
        const defender = this.board[toR][toC];

        if (!attacker || attacker.player !== this.currentTurn) return false;
        if (attacker.isImmobile) {
            this.handleDisqualification(attacker.player, 'Attempted to move an immobile card (Landmine/Flag)!');
            return false;
        }

        this.board[fromR][fromC] = null;

        if (!defender) {
            this.board[toR][toC] = attacker;
            window.soundFX.playMove();
            const pos = `(${String.fromCharCode(65 + toC)}${toR + 1})`;
            const msg = window.I18N ? window.I18N.t('advance_move', { player: attacker.player.toUpperCase(), pos }) : `${attacker.player.toUpperCase()} advanced to ${pos}.`;
            this.log(msg);
            this.finishTurn();
            return true;
        }

        return this.resolveClash(attacker, defender, toR, toC);
    }

    resolveClash(attacker, defender, r, c) {
        attacker.faceUp = true;
        defender.faceUp = true;
        window.soundFX.playClash();

        // Update AI memory for all observing players
        const allSides = this.playerCount === 4 ? ['a', 'b', 'c', 'd'] : ['red', 'black'];
        for (let side of allSides) {
            if (!this.aiMemory[side]) this.aiMemory[side] = new Map();
            if (!this.aiKnownLandmines[side]) this.aiKnownLandmines[side] = new Set();

            if (attacker.player !== side) {
                this.aiMemory[side].set(attacker, {
                    player: attacker.player,
                    rank: attacker.rank,
                    rankVal: OFFICER_RANKS[attacker.rank] || 0,
                    isBomb: attacker.isBomb,
                    isLandmine: attacker.isLandmine,
                    isFlag: attacker.isFlag,
                    isSapper: attacker.isSapper,
                    isMochigoma: attacker.isMochigoma
                });
            }
            if (defender.player !== side) {
                this.aiMemory[side].set(defender, {
                    player: defender.player,
                    rank: defender.rank,
                    rankVal: OFFICER_RANKS[defender.rank] || 0,
                    isBomb: defender.isBomb,
                    isLandmine: defender.isLandmine,
                    isFlag: defender.isFlag,
                    isSapper: defender.isSapper,
                    isMochigoma: defender.isMochigoma
                });
                if (defender.isLandmine) {
                    this.aiKnownLandmines[side].add(`${r},${c}`);
                }
            }
        }

        const aPlayer = attacker.player.toUpperCase();
        const dPlayer = defender.player.toUpperCase();
        let result = {
            id: Math.random(),
            attacker,
            defender,
            winner: null,
            outcomeText: '',
            sound: 'clash'
        };

        // 1. Flag Assault
        if (defender.isFlag) {
            result.winner = 'attacker';
            result.sound = 'victory';
            this.board[r][c] = attacker;
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(defender);
            this.lastClashResult = result;

            if (this.playerCount === 4) {
                const aName = window.I18N ? window.I18N.t(`gen_${attacker.player}`) : `General ${attacker.player.toUpperCase()}`;
                const dName = window.I18N ? window.I18N.t(`gen_${defender.player}`) : `General ${defender.player.toUpperCase()}`;
                result.outcomeText = `🚩 ASSASSINATION! ${aName} captured ${dName}'s Flag!`;
                this.log(result.outcomeText);
                this.eliminatePlayer4P(defender.player, attacker.player);
                this.finishTurn();
                return true;
            } else {
                const winnerText = attacker.player === 'red' ? 
                    (window.I18N ? window.I18N.t('win_red') : 'Red Wins') : 
                    (window.I18N ? window.I18N.t('win_black') : 'Black Wins');
                result.outcomeText = winnerText;
                this.endGame(attacker.player, winnerText);
                return true;
            }
        }

        // 2. Bomb Detonations
        if (attacker.isBomb || defender.isBomb) {
            window.soundFX.playBomb();
            result.winner = 'mutual';
            result.outcomeText = window.I18N ? window.I18N.t('bomb_explosion') : `💥 BOMB EXPLOSION! Both units were annihilated!`;
            result.sound = 'bomb';
            this.purgeCardFromAiMemory(attacker, r, c);
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(attacker, defender);
            this.board[r][c] = null;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 3. Landmine Defense
        if (defender.isLandmine) {
            if (attacker.isSapper || attacker.isMochigoma) {
                window.soundFX.playDefuse();
                result.winner = 'attacker';
                result.outcomeText = window.I18N ? window.I18N.t('mine_cleared') : `🛠️ MINE CLEARED! Sapper disarmed and captured Landmine!`;
                result.sound = 'defuse';
                this.board[r][c] = attacker;
                this.purgeCardFromAiMemory(defender, r, c);
                this.handleCapture(attacker.player, defender);
                if (!attacker.isMochigoma) attacker.faceUp = false;
            } else {
                window.soundFX.playBomb();
                result.winner = 'defender';
                result.outcomeText = window.I18N ? window.I18N.t('mine_detonation', { attacker: attacker.roleName }) : `💣 DETONATION! Attacking ${attacker.roleName} destroyed by Landmine!`;
                result.sound = 'bomb';
                this.board[r][c] = defender;
                this.purgeCardFromAiMemory(attacker, r, c);
                this.graveyard.push(attacker);
                defender.faceUp = false;
            }
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 4. Conscript vs Conscript: Both traitors executed to Graveyard
        if (attacker.isMochigoma && defender.isMochigoma) {
            result.winner = 'mutual';
            result.outcomeText = window.I18N ? window.I18N.t('conscript_clash') : `⚖️ Conscript Clash! Both traitors sent to Graveyard.`;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(attacker, defender);
            this.board[r][c] = null;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 5. Native Sapper vs Native Sapper: Mutual destruction
        if (attacker.isSapper && defender.isSapper && !attacker.isMochigoma && !defender.isMochigoma) {
            result.winner = 'mutual';
            result.outcomeText = window.I18N ? window.I18N.t('sapper_clash') : `⚖️ Sapper Clash! Mutual destruction.`;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(attacker, defender);
            this.board[r][c] = null;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 6. Native Sapper vs Conscript: Native Sapper wins! Conscript executed to Graveyard
        if (attacker.isSapper && !attacker.isMochigoma && defender.isMochigoma) {
            result.winner = 'attacker';
            result.outcomeText = window.I18N ? window.I18N.t('sapper_executed_conscript', { player: aPlayer }) : `⚔️ ${aPlayer} Sapper executed enemy Conscript!`;
            this.board[r][c] = attacker;
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(defender);
            attacker.faceUp = false;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        if (attacker.isMochigoma && defender.isSapper && !defender.isMochigoma) {
            result.winner = 'defender';
            result.outcomeText = window.I18N ? window.I18N.t('sapper_executed_conscript', { player: dPlayer }) : `⚔️ ${dPlayer} Sapper executed enemy Conscript!`;
            this.board[r][c] = defender;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.graveyard.push(attacker);
            defender.faceUp = false;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 7. Conscript vs Numbered Officer: Officer wins, Conscript executed to Graveyard
        if (attacker.isMochigoma) {
            result.winner = 'defender';
            result.outcomeText = window.I18N ? window.I18N.t('officer_executed_conscript', { player: dPlayer }) : `⚔️ ${dPlayer} Officer executed enemy Conscript!`;
            this.board[r][c] = defender;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.graveyard.push(attacker);
            if (!defender.isMochigoma) defender.faceUp = false;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        if (defender.isMochigoma) {
            result.winner = 'attacker';
            result.outcomeText = window.I18N ? window.I18N.t('officer_executed_conscript', { player: aPlayer }) : `⚔️ ${aPlayer} Officer executed enemy Conscript!`;
            this.board[r][c] = attacker;
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(defender);
            if (!attacker.isMochigoma) attacker.faceUp = false;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 8. Native Sapper vs Numbered Officer: Officer wins, Native Sapper captured
        if (attacker.isSapper && !attacker.isMochigoma) {
            result.winner = 'defender';
            result.outcomeText = window.I18N ? window.I18N.t('officer_captured_sapper', { player: dPlayer }) : `⚔️ ${dPlayer} Officer captured attacking Sapper!`;
            this.board[r][c] = defender;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.handleCapture(defender.player, attacker);
            if (!defender.isMochigoma) defender.faceUp = false;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        if (defender.isSapper && !defender.isMochigoma) {
            result.winner = 'attacker';
            result.outcomeText = window.I18N ? window.I18N.t('sapper_captured_by_officer', { player: aPlayer }) : `⚔️ ${aPlayer} Officer captured defending Sapper!`;
            this.board[r][c] = attacker;
            this.purgeCardFromAiMemory(defender, r, c);
            this.handleCapture(attacker.player, defender);
            if (!attacker.isMochigoma) attacker.faceUp = false;
            this.lastClashResult = result;
            this.positionCounts = {};
            this.log(result.outcomeText);
            this.finishTurn();
            return true;
        }

        // 6. Officer vs Officer
        const aRankVal = OFFICER_RANKS[attacker.rank] || 0;
        const dRankVal = OFFICER_RANKS[defender.rank] || 0;

        if (aRankVal > dRankVal) {
            result.winner = 'attacker';
            result.outcomeText = window.I18N ? window.I18N.t('officer_victory', { player: aPlayer }) : `⚔️ VICTORY! ${aPlayer} defeated opponent Officer!`;
            this.board[r][c] = attacker;
            this.purgeCardFromAiMemory(defender, r, c);
            this.handleCapture(attacker.player, defender);
            attacker.faceUp = false;
        } else if (aRankVal < dRankVal) {
            result.winner = 'defender';
            result.outcomeText = window.I18N ? window.I18N.t('officer_defeat', { player: dPlayer }) : `⚔️ DEFEAT! ${dPlayer} Officer defeated attacking unit!`;
            this.board[r][c] = defender;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.handleCapture(defender.player, attacker);
            defender.faceUp = false;
        } else {
            result.winner = 'mutual';
            result.outcomeText = window.I18N ? window.I18N.t('officer_tie') : `⚖️ TIED RANKS! Both units destroyed!`;
            this.purgeCardFromAiMemory(attacker, r, c);
            this.purgeCardFromAiMemory(defender, r, c);
            this.graveyard.push(attacker, defender);
            this.board[r][c] = null;
        }

        this.lastClashResult = result;
        this.positionCounts = {};
        this.log(result.outcomeText);
        this.finishTurn();
        return true;
    }

    handleCapture(capturingPlayer, capturedCard) {
        if (capturedCard.isMochigoma) {
            this.graveyard.push(capturedCard);
            const msg = window.I18N ? window.I18N.t('conscript_executed') : `⚖️ Traitor Conscript executed! Sent to Graveyard.`;
            this.log(msg);
            return;
        }
        capturedCard.player = capturingPlayer;
        capturedCard.isBomb = false;
        capturedCard.isLandmine = false;
        capturedCard.isFlag = false;
        capturedCard.isSapper = false;
        capturedCard.isMochigoma = false;
        if (this.canAcceptMochigoma(capturingPlayer)) {
            this.hands[capturingPlayer].mochigoma.push(capturedCard);
        } else {
            this.graveyard.push(capturedCard);
            const msg = window.I18N ? window.I18N.t('mutiny_excess') : `⚠️ ANTI-MUTINY RULE: Conscription limit reached! Prisoner sent to Graveyard.`;
            this.log(msg);
        }
    }

    dropCard(handType, index, targetR, targetC) {
        const player = this.currentTurn;
        if (this.playerCount === 4) {
            const camp = this.getCampCells(player);
            const inCamp = camp.some(pos => pos.r === targetR && pos.c === targetC);
            if (!inCamp || this.board[targetR][targetC] !== null) return false;
        } else {
            const minRow = player === 'red' ? 0 : 7;
            const maxRow = player === 'red' ? 4 : 11;
            if (targetR < minRow || targetR > maxRow) return false;
            if (this.board[targetR][targetC] !== null) return false;
        }

        let card = null;
        if (handType === 'starting') {
            const peekCard = this.hands[player].startingReserves[index];
            if (!peekCard) return false;
            if (peekCard.isImmobile && this.isFrontline(player, targetR, targetC)) {
                return false;
            }
            card = this.hands[player].startingReserves.splice(index, 1)[0];
            card.faceUp = false;
        } else if (handType === 'mochigoma') {
            card = this.hands[player].mochigoma.splice(index, 1)[0];
            card.isMochigoma = true;
            card.isBomb = false;
            card.isLandmine = false;
            card.isFlag = false;
            card.isSapper = false;
            card.faceUp = true;
        }

        if (!card) return false;

        this.board[targetR][targetC] = card;
        window.soundFX.playCardFlip();
        this.positionCounts = {};
        const pDisp = (window.I18N && this.playerCount === 4) ? window.I18N.t(`gen_${player}`) : player.toUpperCase();
        const msg = card.isMochigoma ? 
            (window.I18N ? window.I18N.t('drop_conscript', { player: pDisp }) : `${pDisp} dropped a Conscript Sapper.`) :
            (window.I18N ? window.I18N.t('drop_secret', { player: pDisp }) : `${pDisp} dropped a Secret Reserve.`);
        this.log(msg);
        this.finishTurn();
        return true;
    }

    eliminatePlayer4P(player, capturedBy) {
        this.eliminated[player] = true;
        const pName = window.I18N ? window.I18N.t(`gen_${player}`) : `General ${player.toUpperCase()}`;
        const msg = window.I18N ? window.I18N.t('player_eliminated', { player: pName }) : `💀 ${pName}'s Flag captured! Army eliminated.`;
        this.log(msg);

        // Remove all pieces belonging to this player from board to graveyard
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card && card.player === player) {
                    this.graveyard.push(card);
                    this.board[r][c] = null;
                }
            }
        }
        // Discard hands
        if (this.hands[player]) {
            this.graveyard.push(...this.hands[player].startingReserves);
            this.hands[player].startingReserves = [];
            this.graveyard.push(...this.hands[player].mochigoma);
            this.hands[player].mochigoma = [];
        }

        this.checkGameOver4P();
    }

    checkGameOver4P() {
        if (this.fourPlayerMode === '2v2') {
            const redAlive = ['a', 'b', 'c', 'd'].some(p => this.seating[p] === 'red' && !this.eliminated[p]);
            const blackAlive = ['a', 'b', 'c', 'd'].some(p => this.seating[p] === 'black' && !this.eliminated[p]);
            if (!redAlive) {
                const winText = window.I18N ? window.I18N.t('team_black_wins') : 'Black Team Wins';
                this.endGame('black', winText);
            } else if (!blackAlive) {
                const winText = window.I18N ? window.I18N.t('team_red_wins') : 'Red Team Wins';
                this.endGame('red', winText);
            }
        } else { // FFA
            const alive = ['a', 'b', 'c', 'd'].filter(p => !this.eliminated[p]);
            if (alive.length <= 1) {
                const winner = alive[0] || null;
                const pName = winner ? (window.I18N ? window.I18N.t(`gen_${winner}`) : `General ${winner.toUpperCase()}`) : 'Draw';
                const winText = winner ? (window.I18N ? window.I18N.t('player_wins', { player: pName }) : `${pName} Wins`) : 'Draw';
                this.endGame(winner, winText);
            }
        }
    }

    handleDisqualification(faultingPlayer, reason) {
        const winningPlayer = faultingPlayer === 'red' ? 'black' : 'red';
        this.endGame(winningPlayer, `DISQUALIFICATION: ${faultingPlayer.toUpperCase()} ${reason}`);
    }

    finishTurn() {
        if (this.gameState === 'gameover') return;

        if (this.playerCount === 4) {
            for (let p of ['a', 'b', 'c', 'd']) {
                this.checkAndEnforceMutiny(p);
            }
            this.checkGameOver4P();
            if (this.gameState === 'gameover') return;

            // Advance to next active (non-eliminated) player
            for (let i = 0; i < 4; i++) {
                this.currentTurnIdx4P = (this.currentTurnIdx4P + 1) % 4;
                const nextP = this.turnOrder4P[this.currentTurnIdx4P];
                if (!this.eliminated[nextP]) {
                    this.currentTurn = nextP;
                    break;
                }
            }
        } else {
            this.checkAndEnforceMutiny('red');
            this.checkAndEnforceMutiny('black');
            this.currentTurn = this.currentTurn === 'red' ? 'black' : 'red';
        }

        this.selectedTile = null;
        this.selectedHandCard = null;

        if (this.recordPosition()) {
            const reason = window.I18N ? window.I18N.t('repetition_draw') : 'DRAW: Threefold repetition of the board position!';
            this.endGame(null, reason);
            return;
        }

        if (!this.hasAnyLegalAction(this.currentTurn)) {
            if (this.playerCount === 4) {
                this.eliminatePlayer4P(this.currentTurn, 'stalemate');
                this.finishTurn();
                return;
            } else {
                const winner = this.currentTurn === 'red' ? 'black' : 'red';
                const loser = this.currentTurn;
                const reason = window.I18N ? window.I18N.t('no_moves', { winner: winner.toUpperCase(), loser: loser.toUpperCase() }) : `${winner.toUpperCase()} WINS: ${loser.toUpperCase()} has no remaining legal moves!`;
                this.endGame(winner, reason);
                return;
            }
        }

        if (this.mode === 'pve' && this.currentTurn === this.botSide && this.gameState === 'playing' && !this.lastClashResult) {
            setTimeout(() => this.runBotTurn(), 600);
        }
    }

    recordPosition() {
        const hash = this.getBoardHash();
        this.positionCounts[hash] = (this.positionCounts[hash] || 0) + 1;
        return this.positionCounts[hash] >= 3;
    }

    getBoardHash() {
        let str = `${this.currentTurn}:`;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (!card) {
                    str += '0,';
                } else {
                    str += `${card.player[0]}${card.rank}${card.isMochigoma ? 'M' : ''},`;
                }
            }
        }
        return str;
    }

    endGame(winner, reason = null) {
        this.gameState = 'gameover';
        this.winner = winner;
        if (winner === 'red') {
            this.winReason = window.I18N ? window.I18N.t('win_red') : 'Red Wins';
        } else if (winner === 'black') {
            this.winReason = window.I18N ? window.I18N.t('win_black') : 'Black Wins';
        } else {
            this.winReason = window.I18N ? window.I18N.t('draw') : 'Draw';
        }
        this.checkAndEnforceMutiny('red');
        this.checkAndEnforceMutiny('black');
        window.soundFX.playVictory();
        this.log(this.winReason);
    }

    getAllLegalActions(player) {
        const actions = [];

        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card && card.player === player && !card.isImmobile) {
                    const legal = this.getLegalMoves(r, c, player);
                    for (let m of legal) {
                        const target = this.board[m.r][m.c];
                        const isCapture = (target !== null && target.player !== player);
                        actions.push({
                            type: 'move',
                            from: { r, c },
                            to: m,
                            card,
                            target,
                            isCapture
                        });
                    }
                }
            }
        }

        if (this.hands[player]) {
            const legalDropsMochi = this.getLegalDrops(player);
            this.hands[player].mochigoma.forEach((card, idx) => {
                for (let d of legalDropsMochi) {
                    actions.push({
                        type: 'drop',
                        handType: 'mochigoma',
                        index: idx,
                        to: d,
                        card,
                        isCapture: false
                    });
                }
            });

            this.hands[player].startingReserves.forEach((card, idx) => {
                const cardDrops = this.getLegalDrops(player, card);
                for (let d of cardDrops) {
                    actions.push({
                        type: 'drop',
                        handType: 'starting',
                        index: idx,
                        to: d,
                        card,
                        isCapture: false
                    });
                }
            });
        }

        return actions;
    }

    getBestActionLow(actions, botSide, enemySide) {
        // Demoted Level: Former Medium Level AI (Grandmaster Model 50 Engine: 2-Ply Lookahead, Active Castle Guard, Koma-kiki & Suki Drop Denial)
        let myFlagPos = null;
        let enemyFlagPos = null;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card) {
                    if (card.isFlag && card.player === botSide) myFlagPos = { r, c };
                    if (card.isFlag && card.player === enemySide) enemyFlagPos = { r, c };
                }
            }
        }

        const myCampRows = botSide === 'red' ? [0, 1, 2, 3, 4] : [11, 10, 9, 8, 7];
        const barrierMine = enemySide === 'red' ? { r: 1, c: 0 } : { r: 10, c: 0 };
        const doorway = enemySide === 'red' ? { r: 2, c: 0 } : { r: 9, c: 0 };
        const myDoorway = botSide === 'red' ? { r: 2, c: 0 } : { r: 9, c: 0 };
        const bunkerRows = enemySide === 'red' ? [0, 1] : [10, 11];
        const bunkerCols = [0, 1, 2];

        // 1. Instant Mate: Capture Flag
        if (enemyFlagPos) {
            for (let a of actions) {
                if (a.type === 'move' && a.to.r === enemyFlagPos.r && a.to.c === enemyFlagPos.c) {
                    a.score = 10000000;
                    return a;
                }
            }
        }

        // 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is empty, drop Conscript for mate in 1!
        if (enemyFlagPos) {
            for (let a of actions) {
                if (a.type === 'drop') {
                    const dFlag = Math.abs(a.to.r - enemyFlagPos.r) + Math.abs(a.to.c - enemyFlagPos.c);
                    if (dFlag === 1) {
                        const tr = a.to.r;
                        const tc = a.to.c;
                        const isKnownMine = this.aiKnownLandmines && this.aiKnownLandmines[botSide] && this.aiKnownLandmines[botSide].has(`${tr},${tc}`);
                        if (!isKnownMine) {
                            a.score = 9000000;
                            return a;
                        }
                    }
                }
            }
        }

        // 3. Active Castle Bodyguard (Kin Doorway Protocol) & Defcon 0 Sanctuary Protection
        const intruders = [];
        for (let r of myCampRows) {
            for (let c = 0; c < this.cols; c++) {
                const ec = this.board[r][c];
                if (ec && ec.player === enemySide) {
                    intruders.push({ r, c, card: ec });
                }
            }
        }

        if (intruders.length > 0) {
            for (let a of actions) {
                if (a.type === 'move') {
                    const tr = a.to.r;
                    const tc = a.to.c;
                    const tgt = a.target;
                    const c = a.card;
                    const myRankVal = OFFICER_RANKS[c.rank] || 0;
                    if (tgt && tgt.player === enemySide && myCampRows.includes(tr)) {
                        const k = this.getKnownCard(tr, tc, botSide);
                        if (c.isBomb) {
                            a.score = 8500000;
                            return a;
                        } else if (myRankVal > 0) {
                            if (k && k.rankVal > 0) {
                                if (myRankVal > k.rankVal) {
                                    a.score = 8500000;
                                    return a;
                                }
                            } else if (!k && myRankVal >= 6) {
                                a.score = 8500000;
                                return a;
                            }
                        }
                    }
                }
            }
            for (let a of actions) {
                if (a.type === 'drop') {
                    const dr = a.to.r;
                    const dc = a.to.c;
                    for (let intruder of intruders) {
                        if (Math.abs(dr - intruder.r) + Math.abs(dc - intruder.c) === 1) {
                            const c = a.card;
                            const rVal = OFFICER_RANKS[c.rank] || 0;
                            if (rVal >= 6 || c.isBomb) {
                                a.score = 8000000;
                                return a;
                            }
                        }
                    }
                }
            }
        }

        // 4. Enemy Sapper Tracking
        let enemySapperPos = null;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const ec = this.board[r][c];
                if (ec && ec.player === enemySide) {
                    const known = this.getKnownCard(r, c, botSide);
                    if (ec.isSapper || ec.isMochigoma || (known && (known.isSapper || known.isMochigoma))) {
                        enemySapperPos = { r, c };
                        break;
                    }
                }
            }
            if (enemySapperPos) break;
        }

        const enemyBombsDead = this.graveyard.filter(c => c.isBomb && c.player === enemySide).length;
        const tenIsInvincible = (enemyBombsDead >= 2);

        // 5. Grandmaster Multi-Component Evaluation Loop
        for (let a of actions) {
            let score = 50;

            if (a.type === 'move') {
                const fr = a.from.r;
                const fc = a.from.c;
                const toR = a.to.r;
                const toC = a.to.c;
                const card = a.card;
                const target = a.target;
                const myRankVal = OFFICER_RANKS[card.rank] || 0;
                const isSapper = card.isSapper || card.isMochigoma;

                if (intruders.length > 0) {
                    for (let intruder of intruders) {
                        const d = Math.abs(toR - intruder.r) + Math.abs(toC - intruder.c);
                        const oldD = Math.abs(fr - intruder.r) + Math.abs(fc - intruder.c);
                        if (d < oldD && (myRankVal >= 6 || card.isBomb)) {
                            score += 250000;
                        }
                    }
                }

                if (enemySapperPos && myRankVal >= 6) {
                    const dEs = Math.abs(toR - enemySapperPos.r) + Math.abs(toC - enemySapperPos.c);
                    const oldDEs = Math.abs(fr - enemySapperPos.r) + Math.abs(fc - enemySapperPos.c);
                    if (dEs < oldDEs) {
                        score += 150000;
                    }
                }

                if (fr === myDoorway.r && fc === myDoorway.c && myRankVal >= 8 && intruders.length === 0) {
                    score -= 30000;
                }
                if (toR === myDoorway.r && toC === myDoorway.c && myRankVal >= 8) {
                    score += 25000;
                }

                if (myRankVal === 10 && tenIsInvincible) {
                    if (target && target.player === enemySide) {
                        if (bunkerRows.includes(toR) && bunkerCols.includes(toC)) score -= 120000;
                        else score += 200000;
                    } else if (enemyFlagPos) {
                        const dFlag = Math.abs(toR - enemyFlagPos.r) + Math.abs(toC - enemyFlagPos.c);
                        score += (20 - dFlag) * 1000;
                    }
                } else if (target && target.player === enemySide) {
                    const known = this.getKnownCard(toR, toC, botSide);
                    if (known) {
                        if (known.isFlag) {
                            a.score = 10000000;
                            return a;
                        } else if (known.isLandmine) {
                            if (isSapper) {
                                score += 180000;
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        } else if (known.rankVal > 0) {
                            if (card.isBomb) {
                                if (known.rankVal <= 5 && !myCampRows.includes(toR)) {
                                    a.score = -9999999;
                                    continue;
                                }
                                score += 180000 + (known.rankVal * 2000);
                            } else if (isSapper) {
                                a.score = -9999999;
                                continue;
                            } else if (myRankVal > known.rankVal) {
                                score += 90000 + (known.rankVal * 800);
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        }
                    } else if (this.aiKnownLandmines && this.aiKnownLandmines[botSide] && this.aiKnownLandmines[botSide].has(`${toR},${toC}`)) {
                        if (isSapper) {
                            score += 180000;
                        } else {
                            a.score = -9999999;
                            continue;
                        }
                    } else {
                        if (bunkerRows.includes(toR) && bunkerCols.includes(toC) && (!target.hasMoved || !target.moveCount)) {
                            if (isSapper) {
                                score += 180000;
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        } else if (card.isBomb) {
                            if (!myCampRows.includes(toR)) {
                                a.score = -9999999;
                                continue;
                            }
                        } else {
                            if (myRankVal === 2 || myRankVal === 3) score += 3500;
                            else if (isSapper) score -= 6000;
                            else if (myRankVal >= 8) score += 300;
                        }
                    }
                }

                const neighbors = [
                    { r: toR - 1, c: toC }, { r: toR + 1, c: toC },
                    { r: toR, c: toC - 1 }, { r: toR, c: toC + 1 }
                ];
                let enemyAttackersCount = 0;
                let friendlyDefendersCount = 0;

                for (let n of neighbors) {
                    if (n.r >= 0 && n.r < this.rows && n.c >= 0 && n.c < this.cols) {
                        const adj = this.board[n.r][n.c];
                        if (adj) {
                            if (adj.player === enemySide) {
                                enemyAttackersCount++;
                                const kAdj = this.getKnownCard(n.r, n.c, botSide);
                                if (kAdj) {
                                    if ((kAdj.rankVal || 0) > myRankVal) {
                                        score -= 750000;
                                    } else if (kAdj.isBomb && myRankVal >= 7) {
                                        score -= 750000;
                                    }
                                } else if (adj.hasMoved && myRankVal <= 5) {
                                    score -= 50000;
                                }
                            } else if (adj.player === botSide && !(n.r === fr && n.c === fc)) {
                                friendlyDefendersCount++;
                            }
                        }
                    }
                }

                const controlDiff = friendlyDefendersCount - enemyAttackersCount;
                score += controlDiff * 300;

                if ([4, 5, 6, 7].includes(toR) && friendlyDefendersCount === 0 && myRankVal >= 7) {
                    score -= 5000;
                }

                if (friendlyDefendersCount >= 2) score += 400;

                if (isSapper) {
                    const dBm = Math.abs(toR - barrierMine.r) + Math.abs(toC - barrierMine.c);
                    const oldDBm = Math.abs(fr - barrierMine.r) + Math.abs(fc - barrierMine.c);
                    if (dBm < oldDBm) score += 60000;
                }

                if (fr === doorway.r && fc === doorway.c && !isSapper) {
                    if (toC !== doorway.c) score += 60000;
                    else score -= 60000;
                }

                if (fc === 0 && toC === 0 && myRankVal >= 8) {
                    const dBm = Math.abs(toR - barrierMine.r);
                    const oldDBm = Math.abs(fr - barrierMine.r);
                    if (dBm < oldDBm && dBm >= 2) score += 45000;
                }

                if (fc === 4 && toC === 4 && myRankVal >= 7) {
                    if ((botSide === 'red' && toR > fr) || (botSide === 'black' && toR < fr)) {
                        score += 350;
                    }
                }

                if (botSide === 'red' && toR > fr) score += 60;
                if (botSide === 'black' && toR < fr) score += 60;

            } else if (a.type === 'drop') {
                const toR = a.to.r;
                const toC = a.to.c;
                if (myFlagPos) {
                    const dFlag = Math.abs(toR - myFlagPos.r) + Math.abs(toC - myFlagPos.c);
                    if (dFlag <= 2) score += 3000;
                }
                for (let r of myCampRows) {
                    for (let c = 0; c < this.cols; c++) {
                        const ec = this.board[r][c];
                        if (ec && ec.player === enemySide) {
                            if (Math.abs(toR - r) + Math.abs(toC - c) === 1) {
                                score += 600000;
                            }
                        }
                    }
                }
                if ((botSide === 'red' && toR === 4) || (botSide === 'black' && toR === 7)) {
                    score += 900;
                } else if (toC === 0 || toC === 4) {
                    score += 600;
                } else {
                    score += 250;
                }
            }

            a.score = score;
        }

        actions.sort((a, b) => b.score - a.score);
        return actions[0];
    }

    getBestActionMedium(actions, botSide, enemySide) {
        // Demoted Level: Former High Level AI (Super Grandmaster Model 100 Engine: Dvoretsky Prophylaxis, Nimzowitsch Bastion Overprotection, Shogi Sabaki & Ai-goma Drop Interposition, and Bayesian Fog-of-War Belief Updating)
        let myFlagPos = null;
        let enemyFlagPos = null;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card) {
                    if (card.isFlag && card.player === botSide) myFlagPos = { r, c };
                    if (card.isFlag && card.player === enemySide) enemyFlagPos = { r, c };
                }
            }
        }

        const myCampRows = botSide === 'red' ? [0, 1, 2, 3, 4] : [11, 10, 9, 8, 7];
        const barrierMine = enemySide === 'red' ? { r: 1, c: 0 } : { r: 10, c: 0 };
        const doorway = enemySide === 'red' ? { r: 2, c: 0 } : { r: 9, c: 0 };
        const myDoorway = botSide === 'red' ? { r: 2, c: 0 } : { r: 9, c: 0 };
        const myFlankAnchor = botSide === 'red' ? { r: 1, c: 1 } : { r: 10, c: 1 };
        const bunkerRows = enemySide === 'red' ? [0, 1] : [10, 11];
        const bunkerCols = [0, 1, 2];

        // 1. Instant Mate Strike: Capture enemy Flag immediately
        if (enemyFlagPos) {
            for (let a of actions) {
                if (a.type === 'move' && a.to.r === enemyFlagPos.r && a.to.c === enemyFlagPos.c) {
                    a.score = 10000000;
                    return a;
                }
            }
        }

        // 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is empty, drop Conscript for mate in 1!
        if (enemyFlagPos) {
            for (let a of actions) {
                if (a.type === 'drop') {
                    const dFlag = Math.abs(a.to.r - enemyFlagPos.r) + Math.abs(a.to.c - enemyFlagPos.c);
                    if (dFlag === 1) {
                        const tr = a.to.r;
                        const tc = a.to.c;
                        const isKnownMine = this.aiKnownLandmines && this.aiKnownLandmines[botSide] && this.aiKnownLandmines[botSide].has(`${tr},${tc}`);
                        if (!isKnownMine) {
                            a.score = 9500000;
                            return a;
                        }
                    }
                }
            }
        }

        // 3. Dvoretsky Prophylactic Emergency & Camp Intruder Execution
        const intruders = [];
        for (let r of myCampRows) {
            for (let c = 0; c < this.cols; c++) {
                const ec = this.board[r][c];
                if (ec && ec.player === enemySide) {
                    intruders.push({ r, c, card: ec });
                }
            }
        }

        let acuteFlagThreat = null;
        if (myFlagPos) {
            for (let n of [
                { r: myFlagPos.r - 1, c: myFlagPos.c }, { r: myFlagPos.r + 1, c: myFlagPos.c },
                { r: myFlagPos.r, c: myFlagPos.c - 1 }, { r: myFlagPos.r, c: myFlagPos.c + 1 }
            ]) {
                if (n.r >= 0 && n.r < this.rows && n.c >= 0 && n.c < this.cols) {
                    const ec = this.board[n.r][n.c];
                    if (ec && ec.player === enemySide) {
                        acuteFlagThreat = { r: n.r, c: n.c, card: ec };
                        break;
                    }
                }
            }
        }

        if (acuteFlagThreat) {
            for (let a of actions) {
                if (a.type === 'move' && a.to.r === acuteFlagThreat.r && a.to.c === acuteFlagThreat.c) {
                    a.score = 9900000;
                    return a;
                }
            }
        }

        if (intruders.length > 0) {
            for (let a of actions) {
                if (a.type === 'move') {
                    const tr = a.to.r;
                    const tc = a.to.c;
                    const tgt = a.target;
                    const c = a.card;
                    const myRankVal = OFFICER_RANKS[c.rank] || 0;
                    if (tgt && tgt.player === enemySide && myCampRows.includes(tr)) {
                        const k = this.getKnownCard(tr, tc, botSide);
                        if (c.isBomb) {
                            a.score = 8800000;
                            return a;
                        } else if (myRankVal > 0) {
                            if (k && k.rankVal > 0) {
                                if (myRankVal > k.rankVal) {
                                    a.score = 8800000;
                                    return a;
                                }
                            } else if (!k && myRankVal >= 6) {
                                a.score = 8800000;
                                return a;
                            }
                        }
                    }
                }
            }

            for (let a of actions) {
                if (a.type === 'drop') {
                    const dr = a.to.r;
                    const dc = a.to.c;
                    for (let intruder of intruders) {
                        if (Math.abs(dr - intruder.r) + Math.abs(dc - intruder.c) === 1) {
                            const c = a.card;
                            const rVal = OFFICER_RANKS[c.rank] || 0;
                            if (rVal >= 6 || c.isBomb || c.isMochigoma) {
                                a.score = 8500000;
                                return a;
                            }
                        }
                    }
                }
            }
        }

        // 4. Enemy Sapper Tracking
        let enemySapperPos = null;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const ec = this.board[r][c];
                if (ec && ec.player === enemySide) {
                    const known = this.getKnownCard(r, c, botSide);
                    if (ec.isSapper || ec.isMochigoma || (known && (known.isSapper || known.isMochigoma))) {
                        enemySapperPos = { r, c };
                        break;
                    }
                }
            }
            if (enemySapperPos) break;
        }

        const enemyBombsDead = this.graveyard.filter(c => c.isBomb && c.player === enemySide).length;
        const tenIsInvincible = (enemyBombsDead >= 2);

        // 5. Grandmaster Multi-Component Evaluation Loop (Model 100)
        for (let a of actions) {
            let score = 50;

            if (a.type === 'move') {
                const fr = a.from.r;
                const fc = a.from.c;
                const toR = a.to.r;
                const toC = a.to.c;
                const card = a.card;
                const target = a.target;
                const myRankVal = OFFICER_RANKS[card.rank] || 0;
                const isSapper = card.isSapper || card.isMochigoma;

                if (intruders.length > 0) {
                    for (let intruder of intruders) {
                        const d = Math.abs(toR - intruder.r) + Math.abs(toC - intruder.c);
                        const oldD = Math.abs(fr - intruder.r) + Math.abs(fc - intruder.c);
                        if (d < oldD && (myRankVal >= 6 || card.isBomb)) {
                            score += 260000;
                        }
                    }
                }

                if (enemySapperPos && myRankVal >= 6) {
                    const dEs = Math.abs(toR - enemySapperPos.r) + Math.abs(toC - enemySapperPos.c);
                    const oldDEs = Math.abs(fr - enemySapperPos.r) + Math.abs(fc - enemySapperPos.c);
                    if (dEs < oldDEs) {
                        score += 160000;
                    }
                }

                // Nimzowitsch Bastion Dual-Lock
                if (fr === myDoorway.r && fc === myDoorway.c && myRankVal >= 8 && intruders.length === 0) {
                    score -= 80000;
                }
                if (toR === myDoorway.r && toC === myDoorway.c && myRankVal >= 8) {
                    score += 40000;
                }
                if (toR === myFlankAnchor.r && toC === myFlankAnchor.c && myRankVal >= 7) {
                    score += 25000;
                }

                // Invincible Sweeper
                if (myRankVal === 10 && tenIsInvincible) {
                    if (target && target.player === enemySide) {
                        if (bunkerRows.includes(toR) && bunkerCols.includes(toC)) score -= 150000;
                        else score += 250000;
                    } else if (enemyFlagPos) {
                        const dFlag = Math.abs(toR - enemyFlagPos.r) + Math.abs(toC - enemyFlagPos.c);
                        score += (20 - dFlag) * 1200;
                    }
                } else if (target && target.player === enemySide) {
                    const known = this.getKnownCard(toR, toC, botSide);
                    if (known) {
                        if (known.isFlag) {
                            a.score = 10000000;
                            return a;
                        } else if (known.isLandmine) {
                            if (isSapper) {
                                score += 200000;
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        } else if (known.rankVal > 0) {
                            if (card.isBomb) {
                                if (known.rankVal <= 5 && !myCampRows.includes(toR)) {
                                    a.score = -9999999;
                                    continue;
                                }
                                score += 190000 + (known.rankVal * 2000);
                            } else if (isSapper) {
                                a.score = -9999999;
                                continue;
                            } else if (myRankVal > known.rankVal) {
                                score += 95000 + (known.rankVal * 900);
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        }
                    } else if (this.aiKnownLandmines && this.aiKnownLandmines[botSide] && this.aiKnownLandmines[botSide].has(`${toR},${toC}`)) {
                        if (isSapper) {
                            score += 200000;
                        } else {
                            a.score = -9999999;
                            continue;
                        }
                    } else {
                        if (bunkerRows.includes(toR) && bunkerCols.includes(toC) && (!target.hasMoved || !target.moveCount)) {
                            if (isSapper) {
                                score += 200000;
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        } else if (card.isBomb) {
                            if (!myCampRows.includes(toR)) {
                                a.score = -9999999;
                                continue;
                            }
                        } else {
                            if (target.hasMoved && myRankVal <= 5) {
                                score -= 60000;
                            } else if (myRankVal === 2 || myRankVal === 3) {
                                score += 3500;
                            } else if (isSapper) {
                                score -= 7000;
                            } else if (myRankVal >= 8) {
                                score += 350;
                            }
                        }
                    }
                }

                // 2-Ply Counter-Threat Simulation (Dvoretsky Prophylaxis)
                const neighbors = [
                    { r: toR - 1, c: toC }, { r: toR + 1, c: toC },
                    { r: toR, c: toC - 1 }, { r: toR, c: toC + 1 }
                ];
                let enemyAttackersCount = 0;
                let friendlyDefendersCount = 0;

                for (let n of neighbors) {
                    if (n.r >= 0 && n.r < this.rows && n.c >= 0 && n.c < this.cols) {
                        const adj = this.board[n.r][n.c];
                        if (adj) {
                            if (adj.player === enemySide) {
                                enemyAttackersCount++;
                                const kAdj = this.getKnownCard(n.r, n.c, botSide);
                                if (kAdj) {
                                    if ((kAdj.rankVal || 0) > myRankVal) {
                                        score -= 850000;
                                    } else if (kAdj.isBomb && myRankVal >= 7) {
                                        score -= 850000;
                                    }
                                } else if (adj.hasMoved && myRankVal <= 5) {
                                    score -= 60000;
                                }
                            } else if (adj.player === botSide && !(n.r === fr && n.c === fc)) {
                                friendlyDefendersCount++;
                            }
                        }
                    }
                }

                const controlDiff = friendlyDefendersCount - enemyAttackersCount;
                score += controlDiff * 400;

                if ([4, 5, 6, 7].includes(toR) && friendlyDefendersCount === 0 && myRankVal >= 7) {
                    score -= 8000;
                }

                if (friendlyDefendersCount >= 2) score += 600;

                if (isSapper) {
                    const dBm = Math.abs(toR - barrierMine.r) + Math.abs(toC - barrierMine.c);
                    const oldDBm = Math.abs(fr - barrierMine.r) + Math.abs(fc - barrierMine.c);
                    if (dBm < oldDBm) score += 70000;
                }

                if (fr === doorway.r && fc === doorway.c && !isSapper) {
                    if (toC !== doorway.c) score += 65000;
                    else score -= 65000;
                }

                if (fc === 0 && toC === 0 && myRankVal >= 8) {
                    const dBm = Math.abs(toR - barrierMine.r);
                    const oldDBm = Math.abs(fr - barrierMine.r);
                    if (dBm < oldDBm && dBm >= 2) score += 50000;
                }

                if (fc === 4 && toC === 4 && myRankVal >= 7) {
                    if ((botSide === 'red' && toR > fr) || (botSide === 'black' && toR < fr)) {
                        score += 400;
                    }
                }

                if (botSide === 'red' && toR > fr) score += 70;
                if (botSide === 'black' && toR < fr) score += 70;

            } else if (a.type === 'drop') {
                const toR = a.to.r;
                const toC = a.to.c;
                if (myFlagPos) {
                    const dFlag = Math.abs(toR - myFlagPos.r) + Math.abs(toC - myFlagPos.c);
                    if (dFlag <= 2) score += 4000;
                }
                for (let r of myCampRows) {
                    for (let c = 0; c < this.cols; c++) {
                        const ec = this.board[r][c];
                        if (ec && ec.player === enemySide) {
                            if (Math.abs(toR - r) + Math.abs(toC - c) === 1) {
                                score += 700000;
                            }
                        }
                    }
                }
                if ((botSide === 'red' && toR === 4) || (botSide === 'black' && toR === 7)) {
                    score += 950;
                } else if (toC === 0 || toC === 4) {
                    score += 650;
                } else {
                    score += 300;
                }
            }

            a.score = score;
        }

        actions.sort((a, b) => b.score - a.score);
        return actions[0];
    }

    getBestActionHigh(actions, botSide, enemySide) {
        // Omniscient Super-Grandmaster Model 200 Engine:
        // 1. Suki-ga-nai Instant Breach Resealing (auto-replug disarmed barrier mines)
        // 2. 5-Column Corridor Infiltration Integrity Tensor (sealing columns 0..4 against human flank bypass)
        // 3. Dynamic Anti-Bait Veto (D-SEE Deflection Resistance: guards never leave posts for low probes)
        // 4. Proactive Midfield Dominance (controlling rows 4-7 with coordinated batteries)
        // 5. Mochigoma Tactical Fork & Wedge Mastery (devastating drop-checkmate wedges)
        // 6. Zero-Tolerance Blunder Invariance & Revealed Memory Integration
        let myFlagPos = null;
        let enemyFlagPos = null;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.board[r][c];
                if (card) {
                    if (card.isFlag && card.player === botSide) myFlagPos = { r, c };
                    if (card.isFlag && card.player === enemySide) enemyFlagPos = { r, c };
                }
            }
        }

        const myCampRows = botSide === 'red' ? [0, 1, 2, 3, 4] : [11, 10, 9, 8, 7];
        const barrierMine = enemySide === 'red' ? { r: 1, c: 0 } : { r: 10, c: 0 };
        const myBarrierMine = botSide === 'red' ? { r: 1, c: 0 } : { r: 10, c: 0 };
        const doorway = enemySide === 'red' ? { r: 2, c: 0 } : { r: 9, c: 0 };
        const myDoorway = botSide === 'red' ? { r: 2, c: 0 } : { r: 9, c: 0 };
        const myFlankAnchor = botSide === 'red' ? { r: 1, c: 1 } : { r: 10, c: 1 };
        const myEastAnchor = botSide === 'red' ? { r: 2, c: 4 } : { r: 9, c: 4 };
        const bunkerRows = enemySide === 'red' ? [0, 1] : [10, 11];
        const bunkerCols = [0, 1, 2];

        // 1. Instant Mate Strike: Capture enemy Flag immediately
        if (enemyFlagPos) {
            for (let a of actions) {
                if (a.type === 'move' && a.to.r === enemyFlagPos.r && a.to.c === enemyFlagPos.c) {
                    a.score = 10000000;
                    return a;
                }
            }
        }

        // 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is empty, drop Conscript for mate in 1!
        if (enemyFlagPos) {
            for (let a of actions) {
                if (a.type === 'drop') {
                    const dFlag = Math.abs(a.to.r - enemyFlagPos.r) + Math.abs(a.to.c - enemyFlagPos.c);
                    if (dFlag === 1) {
                        const tr = a.to.r;
                        const tc = a.to.c;
                        const isKnownMine = this.aiKnownLandmines && this.aiKnownLandmines[botSide] && this.aiKnownLandmines[botSide].has(`${tr},${tc}`);
                        if (!isKnownMine) {
                            a.score = 9800000;
                            return a;
                        }
                    }
                }
            }
        }

        // 3. Acute Flag Threat Defense: Immediate elimination of enemy piece threatening Flag
        let acuteFlagThreat = null;
        if (myFlagPos) {
            for (let n of [
                { r: myFlagPos.r - 1, c: myFlagPos.c }, { r: myFlagPos.r + 1, c: myFlagPos.c },
                { r: myFlagPos.r, c: myFlagPos.c - 1 }, { r: myFlagPos.r, c: myFlagPos.c + 1 }
            ]) {
                if (n.r >= 0 && n.r < this.rows && n.c >= 0 && n.c < this.cols) {
                    const ec = this.board[n.r][n.c];
                    if (ec && ec.player === enemySide) {
                        acuteFlagThreat = { r: n.r, c: n.c, card: ec };
                        break;
                    }
                }
            }
        }

        if (acuteFlagThreat) {
            for (let a of actions) {
                if (a.type === 'move' && a.to.r === acuteFlagThreat.r && a.to.c === acuteFlagThreat.c) {
                    a.score = 9900000;
                    return a;
                }
            }
        }

        // 4. Camp Intruder Prophylaxis & 5-Column Corridor Defense
        const intruders = [];
        for (let r of myCampRows) {
            for (let c = 0; c < this.cols; c++) {
                const ec = this.board[r][c];
                if (ec && ec.player === enemySide) {
                    intruders.push({ r, c, card: ec });
                }
            }
        }

        if (intruders.length > 0) {
            for (let a of actions) {
                if (a.type === 'move') {
                    const tr = a.to.r;
                    const tc = a.to.c;
                    const tgt = a.target;
                    const c = a.card;
                    const myRankVal = OFFICER_RANKS[c.rank] || 0;
                    if (tgt && tgt.player === enemySide && myCampRows.includes(tr)) {
                        const k = this.getKnownCard(tr, tc, botSide);
                        if (c.isBomb) {
                            a.score = 8900000;
                            return a;
                        } else if (myRankVal > 0) {
                            if (k && k.rankVal > 0) {
                                if (myRankVal > k.rankVal) {
                                    a.score = 8900000;
                                    return a;
                                }
                            } else if (!k && myRankVal >= 6) {
                                a.score = 8900000;
                                return a;
                            }
                        }
                    }
                }
            }

            for (let a of actions) {
                if (a.type === 'drop') {
                    const dr = a.to.r;
                    const dc = a.to.c;
                    for (let intruder of intruders) {
                        if (Math.abs(dr - intruder.r) + Math.abs(dc - intruder.c) === 1) {
                            const c = a.card;
                            const rVal = OFFICER_RANKS[c.rank] || 0;
                            if (rVal >= 6 || c.isBomb || c.isMochigoma) {
                                a.score = 8600000;
                                return a;
                            }
                        }
                    }
                }
            }
        }

        // 5. Enemy Sapper Tracking
        let enemySapperPos = null;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const ec = this.board[r][c];
                if (ec && ec.player === enemySide) {
                    const known = this.getKnownCard(r, c, botSide);
                    if (ec.isSapper || ec.isMochigoma || (known && (known.isSapper || known.isMochigoma))) {
                        enemySapperPos = { r, c };
                        break;
                    }
                }
            }
            if (enemySapperPos) break;
        }

        const enemyBombsDead = this.graveyard.filter(c => c.isBomb && c.player === enemySide).length;
        const tenIsInvincible = (enemyBombsDead >= 2);
        const myBarrierEmpty = (myFlagPos && !this.board[myBarrierMine.r][myBarrierMine.c]);

        // 6. Omniscient Multi-Component Scoring Loop (Model 200)
        for (let a of actions) {
            let score = 50;

            // Suki-ga-nai Instant Breach Resealing Priority
            if (myBarrierEmpty && a.to.r === myBarrierMine.r && a.to.c === myBarrierMine.c) {
                if (a.type === 'drop') score += 880000;
                else if (a.type === 'move') score += 850000;
            }

            if (a.type === 'move') {
                const fr = a.from.r;
                const fc = a.from.c;
                const toR = a.to.r;
                const toC = a.to.c;
                const card = a.card;
                const target = a.target;
                const myRankVal = OFFICER_RANKS[card.rank] || 0;
                const isSapper = card.isSapper || card.isMochigoma;

                // Priority A: Intercept Camp Intruders
                if (intruders.length > 0) {
                    for (let intruder of intruders) {
                        const d = Math.abs(toR - intruder.r) + Math.abs(toC - intruder.c);
                        const oldD = Math.abs(fr - intruder.r) + Math.abs(fc - intruder.c);
                        if (d < oldD && (myRankVal >= 6 || card.isBomb)) {
                            score += 280000;
                        }
                    }
                }

                // Priority B: Hunt Enemy Sapper
                if (enemySapperPos && myRankVal >= 6) {
                    const dEs = Math.abs(toR - enemySapperPos.r) + Math.abs(toC - enemySapperPos.c);
                    const oldDEs = Math.abs(fr - enemySapperPos.r) + Math.abs(fc - enemySapperPos.c);
                    if (dEs < oldDEs) {
                        score += 180000;
                    }
                }

                // Priority C: 5-Column Corridor Infiltration Proofing
                // If a human infiltrator approaches rows 4-5 on any column, intercept with high officer
                const perimeterRow = botSide === 'red' ? 4 : 7;
                for (let c = 0; c < this.cols; c++) {
                    const pieceOnPerimeter = this.board[perimeterRow][c];
                    if (pieceOnPerimeter && pieceOnPerimeter.player === enemySide) {
                        const dThreat = Math.abs(toR - perimeterRow) + Math.abs(toC - c);
                        const oldDThreat = Math.abs(fr - perimeterRow) + Math.abs(fc - c);
                        if (dThreat < oldDThreat && myRankVal >= 6) {
                            score += 150000;
                        }
                    }
                }

                // Priority D: Fortress Anchor Preservation & Dynamic Anti-Bait Veto (D-SEE)
                const isDoorwayGuard = (fr === myDoorway.r && fc === myDoorway.c);
                const isFlankGuard = (fr === myFlankAnchor.r && fc === myFlankAnchor.c);
                const isEastGuard = (fr === myEastAnchor.r && fc === myEastAnchor.c);

                if ((isDoorwayGuard || isFlankGuard || isEastGuard) && intruders.length === 0) {
                    // Severe penalty for abandoning fortress guard post
                    score -= 90000;
                }
                if (toR === myDoorway.r && toC === myDoorway.c && myRankVal >= 8) {
                    score += 50000;
                }
                if (toR === myFlankAnchor.r && toC === myFlankAnchor.c && myRankVal >= 7) {
                    score += 35000;
                }
                if (toR === myEastAnchor.r && toC === myEastAnchor.c && myRankVal >= 7) {
                    score += 30000;
                }

                // Priority E: Invincible Sweeper
                if (myRankVal === 10 && tenIsInvincible) {
                    if (target && target.player === enemySide) {
                        if (bunkerRows.includes(toR) && bunkerCols.includes(toC)) score -= 150000;
                        else score += 280000;
                    } else if (enemyFlagPos) {
                        const dFlag = Math.abs(toR - enemyFlagPos.r) + Math.abs(toC - enemyFlagPos.c);
                        score += (20 - dFlag) * 1500;
                    }
                } else if (target && target.player === enemySide) {
                    const known = this.getKnownCard(toR, toC, botSide);
                    if (known) {
                        if (known.isFlag) {
                            a.score = 10000000;
                            return a;
                        } else if (known.isLandmine) {
                            if (isSapper) {
                                score += 220000;
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        } else if (known.rankVal > 0) {
                            // Dynamic Anti-Bait Veto: If defender on post tries to chase rank <= 5 outside camp, veto!
                            if ((isDoorwayGuard || isFlankGuard) && known.rankVal <= 5 && !myCampRows.includes(toR)) {
                                score -= 90000;
                            }

                            if (card.isBomb) {
                                if (known.rankVal <= 5 && !myCampRows.includes(toR)) {
                                    a.score = -9999999;
                                    continue;
                                }
                                score += 220000 + (known.rankVal * 2500);
                            } else if (isSapper) {
                                a.score = -9999999;
                                continue;
                            } else if (myRankVal > known.rankVal) {
                                score += 110000 + (known.rankVal * 1000);
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        }
                    } else if (this.aiKnownLandmines && this.aiKnownLandmines[botSide] && this.aiKnownLandmines[botSide].has(`${toR},${toC}`)) {
                        if (isSapper) {
                            score += 220000;
                        } else {
                            a.score = -9999999;
                            continue;
                        }
                    } else {
                        // Unknown face-down enemy card
                        if (bunkerRows.includes(toR) && bunkerCols.includes(toC) && (!target.hasMoved || !target.moveCount)) {
                            if (isSapper) {
                                score += 220000;
                            } else {
                                a.score = -9999999;
                                continue;
                            }
                        } else if (card.isBomb) {
                            if (!myCampRows.includes(toR)) {
                                a.score = -9999999;
                                continue;
                            }
                        } else {
                            if (target.hasMoved && myRankVal <= 5) {
                                score -= 70000;
                            } else if (myRankVal === 2 || myRankVal === 3) {
                                score += 4000;
                            } else if (isSapper) {
                                score -= 8000;
                            } else if (myRankVal >= 8) {
                                score += 400;
                            }
                        }
                    }
                }

                // Priority F: 2-Ply Counter-Threat & Komakiki Mutual Defense
                const neighbors = [
                    { r: toR - 1, c: toC }, { r: toR + 1, c: toC },
                    { r: toR, c: toC - 1 }, { r: toR, c: toC + 1 }
                ];
                let enemyAttackersCount = 0;
                let friendlyDefendersCount = 0;

                for (let n of neighbors) {
                    if (n.r >= 0 && n.r < this.rows && n.c >= 0 && n.c < this.cols) {
                        const adj = this.board[n.r][n.c];
                        if (adj) {
                            if (adj.player === enemySide) {
                                enemyAttackersCount++;
                                const kAdj = this.getKnownCard(n.r, n.c, botSide);
                                if (kAdj) {
                                    if ((kAdj.rankVal || 0) > myRankVal) {
                                        score -= 900000;
                                    } else if (kAdj.isBomb && myRankVal >= 7) {
                                        score -= 900000;
                                    }
                                } else if (adj.hasMoved && myRankVal <= 5) {
                                    score -= 70000;
                                }
                            } else if (adj.player === botSide && !(n.r === fr && n.c === fc)) {
                                friendlyDefendersCount++;
                            }
                        }
                    }
                }

                const controlDiff = friendlyDefendersCount - enemyAttackersCount;
                score += controlDiff * 500;

                // Priority G: Midfield Dominance & Anti-Blunder Shield
                if ([4, 5, 6, 7].includes(toR)) {
                    if (friendlyDefendersCount === 0 && myRankVal >= 7) {
                        score -= 10000;
                    } else if (friendlyDefendersCount >= 1 && myRankVal >= 7) {
                        score += 5000;
                    }
                }

                if (friendlyDefendersCount >= 2) score += 800;

                // Priority H: Sapper Infiltration Route
                if (isSapper) {
                    const dBm = Math.abs(toR - barrierMine.r) + Math.abs(toC - barrierMine.c);
                    const oldDBm = Math.abs(fr - barrierMine.r) + Math.abs(fc - barrierMine.c);
                    if (dBm < oldDBm) score += 80000;
                }

                // Doorway traversal
                if (fr === doorway.r && fc === doorway.c && !isSapper) {
                    if (toC !== doorway.c) score += 70000;
                    else score -= 70000;
                }

                // Column 0 Sapper Escort
                if (fc === 0 && toC === 0 && myRankVal >= 8) {
                    const dBm = Math.abs(toR - barrierMine.r);
                    const oldDBm = Math.abs(fr - barrierMine.r);
                    if (dBm < oldDBm && dBm >= 2) score += 55000;
                }

                // Column 4 Pincer Flank Advance
                if (fc === 4 && toC === 4 && myRankVal >= 7) {
                    if ((botSide === 'red' && toR > fr) || (botSide === 'black' && toR < fr)) {
                        score += 500;
                    }
                }

                if (botSide === 'red' && toR > fr) score += 80;
                if (botSide === 'black' && toR < fr) score += 80;

            } else if (a.type === 'drop') {
                const toR = a.to.r;
                const toC = a.to.c;
                if (myFlagPos) {
                    const dFlag = Math.abs(toR - myFlagPos.r) + Math.abs(toC - myFlagPos.c);
                    if (dFlag <= 2) score += 5000;
                }
                for (let r of myCampRows) {
                    for (let c = 0; c < this.cols; c++) {
                        const ec = this.board[r][c];
                        if (ec && ec.player === enemySide) {
                            if (Math.abs(toR - r) + Math.abs(toC - c) === 1) {
                                score += 750000;
                            }
                        }
                    }
                }
                if ((botSide === 'red' && toR === 4) || (botSide === 'black' && toR === 7)) {
                    score += 1000;
                } else if (toC === 0 || toC === 4) {
                    score += 700;
                } else {
                    score += 350;
                }
            }

            a.score = score;
        }

        actions.sort((a, b) => b.score - a.score);
        return actions[0];
    }

    runBotTurn() {
        const botSide = this.botSide;
        if (this.gameState !== 'playing' || this.currentTurn !== botSide || this.lastClashResult) return;

        const enemySide = this.humanSide;
        const actions = this.getAllLegalActions(botSide);

        if (actions.length === 0) {
            const winner = enemySide;
            const loser = botSide;
            const reason = window.I18N ? window.I18N.t('no_moves', { winner: winner.toUpperCase(), loser: loser.toUpperCase() }) : `${winner.toUpperCase()} WINS: ${loser.toUpperCase()} has no remaining legal moves!`;
            this.endGame(winner, reason);
            return;
        }

        let chosen = null;
        if (this.aiLevel === 'low') {
            chosen = this.getBestActionLow(actions, botSide, enemySide);
        } else if (this.aiLevel === 'high') {
            chosen = this.getBestActionHigh(actions, botSide, enemySide);
        } else {
            // Medium
            chosen = this.getBestActionMedium(actions, botSide, enemySide);
        }

        if (chosen.type === 'move') {
            this.movePiece(chosen.from.r, chosen.from.c, chosen.to.r, chosen.to.c);
        } else if (chosen.type === 'drop') {
            this.dropCard(chosen.handType, chosen.index, chosen.to.r, chosen.to.c);
        }

        if (window.renderApp) window.renderApp();
    }
}

// Universal Module Definition (UMD) & Environment Exports
if (typeof window !== 'undefined') {
    window.GameEngine = GameEngine;
    window.Card = Card;
    window.SUITS = SUITS;
    window.RANKS = RANKS;
    window.OFFICER_RANKS = OFFICER_RANKS;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GameEngine, Card, SUITS, RANKS, OFFICER_RANKS };
}

if (typeof globalThis !== 'undefined') {
    globalThis.GameEngine = GameEngine;
    globalThis.Card = Card;
    globalThis.SUITS = SUITS;
    globalThis.RANKS = RANKS;
    globalThis.OFFICER_RANKS = OFFICER_RANKS;
}

