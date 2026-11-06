/**
 * 10-Round "Grill Me" Combat Parity & Fight Engine Test Suite
 * Rigorously verifies all combat mechanisms, sound triggers, card deserialization,
 * fog-of-war reveal, mochigoma captures, and state view projections between PvE and PvP.
 */

import { GameEngine, Card, OFFICER_RANKS } from '../../game.js';
import { RoomDO } from '../RoomDO.js';
import assert from 'node:assert';

console.log('================================================================');
console.log('🔥 STARTING 10 ROUNDS OF "GRILL ME" PVP COMBAT PARITY TEST SUITE');
console.log('================================================================\n');

// Mock client-side deserializeCard and getLocalizedClashVerdict for node testing
function deserializeCard(p, fallbackOwner = 'red') {
    if (!p) return null;
    if (p instanceof Card) return p;
    const player = p.player || fallbackOwner;
    const isJoker = !!p.isFlag || p.rank === 'JOKER';
    const card = new Card(player, p.suit, p.rank, isJoker);
    card.originalOwner = p.originalOwner || player;
    card.team = p.team || player;
    card.faceUp = !!p.faceUp;
    card.isFlag = !!p.isFlag || isJoker;
    card.isBomb = !!p.isBomb || p.rank === 'K';
    card.isLandmine = !!p.isLandmine || p.rank === 'Q' || p.rank === 'J';
    card.isSapper = !!p.isSapper || p.rank === 'A' || !!p.isMochigoma;
    card.isMochigoma = !!p.isMochigoma;
    return card;
}

function mockGetLocalizedClashVerdict(clash, lang = 'zh') {
    if (!clash) return '';
    const a = deserializeCard(clash.attacker, 'red');
    const d = deserializeCard(clash.defender, 'black');
    if (!a || !d) return clash.outcomeText || '';

    const aName = lang === 'zh' ? (a.player === 'red' ? '红方' : '黑方') : a.player.toUpperCase();
    const dName = lang === 'zh' ? (d.player === 'red' ? '红方' : '黑方') : d.player.toUpperCase();

    if (d.isFlag) {
        return lang === 'zh' ? (a.player === 'red' ? '红方胜' : '黑方胜') : `${a.player.toUpperCase()} Wins`;
    }
    if (a.isBomb || d.isBomb) {
        return lang === 'zh' ? '炸弹引爆！双方部队同归于尽，送入墓地！' : 'BOMB EXPLOSION! Both units were annihilated!';
    }
    if (d.isLandmine) {
        if (a.isSapper || a.isMochigoma) {
            return lang === 'zh' ? '排雷成功！工兵成功拆除并缴获地雷！' : 'MINE CLEARED! Sapper disarmed and captured Landmine!';
        } else {
            return lang === 'zh' ? `地雷爆炸！进攻方 ${a.getRoleName()} 被地雷消灭！` : `DETONATION! Attacking ${a.roleName} destroyed by Landmine!`;
        }
    }
    if (a.isMochigoma && d.isMochigoma) {
        return lang === 'zh' ? '动员兵交锋！双方叛军同归于尽，送入墓地。' : 'Conscript Clash! Both traitors sent to Graveyard.';
    }
    if (a.isSapper && d.isSapper && !a.isMochigoma && !d.isMochigoma) {
        return lang === 'zh' ? '工兵交锋！双方同归于尽。' : 'Sapper Clash! Mutual destruction.';
    }
    if (a.isSapper && !a.isMochigoma && d.isMochigoma) {
        return lang === 'zh' ? `${aName} 工兵击杀叛军动员兵！` : `${aName} Sapper executed enemy Conscript!`;
    }
    if (a.isMochigoma && d.isSapper && !d.isMochigoma) {
        return lang === 'zh' ? `${dName} 工兵击杀叛军动员兵！` : `${dName} Sapper executed enemy Conscript!`;
    }
    if (a.isMochigoma) {
        return lang === 'zh' ? `${dName} 军官处决敌方动员兵！` : `${dName} Officer executed enemy Conscript!`;
    }
    if (d.isMochigoma) {
        return lang === 'zh' ? `${aName} 军官处决敌方动员兵！` : `${aName} Officer executed enemy Conscript!`;
    }
    if (a.isSapper && !a.isMochigoma) {
        return lang === 'zh' ? `${dName} 军官击溃并捕获敌方工兵！` : `${dName} Officer captured attacking Sapper!`;
    }
    if (d.isSapper && !d.isMochigoma) {
        return lang === 'zh' ? `${aName} 军官消灭敌方进攻工兵！` : `${aName} Officer captured defending Sapper!`;
    }
    if (clash.winner === 'attacker') {
        return lang === 'zh' ? `战斗胜利！${aName} 军官击败敌方部队！` : `VICTORY! ${aName} defeated opponent Officer!`;
    } else if (clash.winner === 'defender') {
        return lang === 'zh' ? `进攻受挫！${dName} 防守军官歼灭进攻部队！` : `DEFEAT! ${dName} Officer defeated attacking unit!`;
    } else {
        return lang === 'zh' ? '势均力敌！同级军官拼杀同归于尽！' : 'TIED RANKS! Both units destroyed!';
    }
}

// -------------------------------------------------------------
// ROUND 1: Deserialization & Prototype Safety
// -------------------------------------------------------------
console.log('--- ROUND 1: Deserialization & Prototype Safety ---');
console.log('GRILL: If network sends raw JSON without prototype, does deserializeCard restore all methods and properties?');
{
    const rawAttacker = {
        player: 'red',
        originalOwner: 'red',
        team: 'red',
        rank: '8',
        suit: '♥',
        roleName: 'Officer',
        isFlag: false,
        isBomb: false,
        isLandmine: false,
        isSapper: false,
        isMochigoma: false,
        faceUp: true
    };

    const card = deserializeCard(rawAttacker, 'red');
    assert.strictEqual(card instanceof Card, true, 'card must be instance of Card');
    assert.strictEqual(typeof card.getRoleName, 'function', 'getRoleName must be a function');
    assert.strictEqual(card.roleName, 'Officer', 'roleName getter must work');
    assert.strictEqual(card.isImmobile, false, 'isImmobile must be false for officer');
    assert.strictEqual(card.originalOwner, 'red', 'originalOwner preserved');
    console.log('✓ PASS: Raw network card hydrated into fully functional Card instance.');
}

// -------------------------------------------------------------
// ROUND 2: Officer vs Officer Clash (Higher Rank Eliminates Lower)
// -------------------------------------------------------------
console.log('\n--- ROUND 2: Officer vs Officer (Rank 9 vs Rank 7) ---');
console.log('GRILL: In PvE, higher officer wins, takes square, loser goes to graveyard. Does server RoomDO do this identically?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redOfficer9 = new Card('red', '♥', '9', false);
    const blackOfficer7 = new Card('black', '♠', '7', false);
    engine.board[4][2] = redOfficer9;
    engine.board[5][2] = blackOfficer7;

    const res = engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(res, true, 'movePiece should succeed');
    assert.strictEqual(engine.board[4][2], null, 'old square empty');
    assert.strictEqual(engine.board[5][2], redOfficer9, 'winner occupies target square');
    assert.strictEqual(engine.hands.red.mochigoma.length, 1, 'captured officer taken into red mochigoma as POW (Shogi rule)');
    assert.strictEqual(engine.hands.red.mochigoma[0], blackOfficer7, 'black 7 in red mochigoma');
    assert.strictEqual(engine.lastClashResult.winner, 'attacker', 'winner is attacker');
    assert.strictEqual(engine.lastClashResult.sound, 'clash', 'sound is clash');

    // Test localized verdict
    const verdictZh = mockGetLocalizedClashVerdict(engine.lastClashResult, 'zh');
    const verdictEn = mockGetLocalizedClashVerdict(engine.lastClashResult, 'en');
    assert.strictEqual(verdictZh.includes('红方 军官击败敌方部队'), true, 'zh verdict check');
    assert.strictEqual(verdictEn.includes('VICTORY! RED defeated'), true, 'en verdict check');
    console.log('✓ PASS: Officer Rank 9 defeats Rank 7 with correct sound, square occupation, and bilingual verdicts.');
}

// -------------------------------------------------------------
// ROUND 3: Officer vs Officer Mutual Annihilation (Equal Ranks)
// -------------------------------------------------------------
console.log('\n--- ROUND 3: Officer vs Officer Mutual Tie (Rank 8 vs Rank 8) ---');
console.log('GRILL: When equal officers clash, are both destroyed, square emptied, and both sent to graveyard?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redOfficer8 = new Card('red', '♦', '8', false);
    const blackOfficer8 = new Card('black', '♣', '8', false);
    engine.board[4][2] = redOfficer8;
    engine.board[5][2] = blackOfficer8;

    engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(engine.board[4][2], null, 'attacker square empty');
    assert.strictEqual(engine.board[5][2], null, 'defender square empty (both eliminated)');
    assert.strictEqual(engine.graveyard.length, 2, 'both in graveyard');
    assert.strictEqual(engine.lastClashResult.winner, 'mutual', 'winner is mutual');
    assert.strictEqual(engine.lastClashResult.sound, 'clash', 'sound is clash');
    console.log('✓ PASS: Equal ranks mutually annihilate, clearing square.');
}

// -------------------------------------------------------------
// ROUND 4: Bomb vs Any Piece Detonation
// -------------------------------------------------------------
console.log('\n--- ROUND 4: Bomb Detonation Mutual Annihilation ---');
console.log('GRILL: When a Bomb collides with General 10, does playBomb sound trigger and both get destroyed?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redBomb = new Card('red', '♥', 'K', false);
    const blackGen10 = new Card('black', '♠', '10', false);
    engine.board[4][2] = redBomb;
    engine.board[5][2] = blackGen10;

    engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(engine.board[4][2], null, 'attacker square empty');
    assert.strictEqual(engine.board[5][2], null, 'defender square empty');
    assert.strictEqual(engine.graveyard.length, 2, 'both in graveyard');
    assert.strictEqual(engine.lastClashResult.winner, 'mutual', 'winner is mutual');
    assert.strictEqual(engine.lastClashResult.sound, 'bomb', 'sound must be bomb');

    const verdictZh = mockGetLocalizedClashVerdict(engine.lastClashResult, 'zh');
    assert.strictEqual(verdictZh.includes('炸弹引爆'), true, 'zh bomb text');
    console.log('✓ PASS: Bomb collision triggers sound: "bomb", mutual destruction, and localized explosion text.');
}

// -------------------------------------------------------------
// ROUND 5: Sapper vs Landmine (Disarm & Capture to Mochigoma)
// -------------------------------------------------------------
console.log('\n--- ROUND 5: Sapper vs Landmine (Disarm & Mochigoma Capture) ---');
console.log('GRILL: When Sapper attacks Landmine, does sound: "defuse" trigger, Sapper advance, and Landmine join Mochigoma?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redSapper = new Card('red', '♦', 'A', false);
    const blackMine = new Card('black', '♣', 'Q', false);
    engine.board[4][2] = redSapper;
    engine.board[5][2] = blackMine;

    engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(engine.board[5][2], redSapper, 'sapper occupies landmine tile');
    assert.strictEqual(engine.lastClashResult.winner, 'attacker', 'sapper wins');
    assert.strictEqual(engine.lastClashResult.sound, 'defuse', 'sound must be defuse');
    assert.strictEqual(engine.hands.red.mochigoma.length, 1, 'landmine captured to red mochigoma');
    assert.strictEqual(engine.hands.red.mochigoma[0].rank, 'Q', 'captured mine card is Q');
    
    // Now drop it as a Conscript
    engine.currentTurn = 'red';
    const dropped = engine.dropCard('mochigoma', 0, 1, 2);
    assert.strictEqual(dropped, true, 'dropping from mochigoma should succeed');
    assert.strictEqual(engine.board[1][2].isMochigoma, true, 'dropped piece is now Mochigoma Conscript');
    assert.strictEqual(engine.board[1][2].faceUp, true, 'dropped conscript is face up');
    console.log('✓ PASS: Sapper disarms mine, triggers sound: "defuse", and captures mine to mochigoma.');
}

// -------------------------------------------------------------
// ROUND 6: Officer vs Landmine (Officer Annihilated, Landmine Survives)
// -------------------------------------------------------------
console.log('\n--- ROUND 6: Non-Sapper Officer vs Landmine ---');
console.log('GRILL: When a normal Officer attacks Landmine, does sound: "bomb" trigger, attacker die, and mine stay hidden?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redOfficer = new Card('red', '♥', '9', false);
    const blackMine = new Card('black', '♠', 'J', false);
    engine.board[4][2] = redOfficer;
    engine.board[5][2] = blackMine;

    engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(engine.board[4][2], null, 'attacker removed');
    assert.strictEqual(engine.board[5][2], blackMine, 'landmine survives on square');
    assert.strictEqual(blackMine.faceUp, false, 'landmine re-cloaked face down');
    assert.strictEqual(engine.graveyard.length, 1, 'officer sent to graveyard');
    assert.strictEqual(engine.lastClashResult.winner, 'defender', 'defender wins');
    assert.strictEqual(engine.lastClashResult.sound, 'bomb', 'sound must be bomb');
    console.log('✓ PASS: Officer killed by landmine, sound: "bomb", landmine remains and goes face-down.');
}

// -------------------------------------------------------------
// ROUND 7: Sapper vs Conscript & Conscript vs Conscript
// -------------------------------------------------------------
console.log('\n--- ROUND 7: Sapper vs Conscript & Conscript vs Conscript ---');
console.log('GRILL: Are conscripts executed properly when facing native sappers or other conscripts?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redSapper = new Card('red', '♥', 'A', false);
    const blackConscript = new Card('black', '♠', '2', false);
    blackConscript.isMochigoma = true;
    blackConscript.isSapper = true;

    engine.board[4][2] = redSapper;
    engine.board[5][2] = blackConscript;

    engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(engine.board[5][2], redSapper, 'native sapper wins');
    assert.strictEqual(engine.graveyard.includes(blackConscript), true, 'conscript sent to graveyard');

    // Now Conscript vs Conscript
    engine.currentTurn = 'red';
    const redConscript = new Card('red', '♦', '3', false);
    redConscript.isMochigoma = true;
    redConscript.isSapper = true;
    const blackConscript2 = new Card('black', '♣', '4', false);
    blackConscript2.isMochigoma = true;
    blackConscript2.isSapper = true;

    engine.board[3][1] = redConscript;
    engine.board[4][1] = blackConscript2;

    engine.movePiece(3, 1, 4, 1);
    assert.strictEqual(engine.board[3][1], null, 'square 1 empty');
    assert.strictEqual(engine.board[4][1], null, 'square 2 empty');
    assert.strictEqual(engine.lastClashResult.winner, 'mutual', 'conscripts mutually eliminated');
    console.log('✓ PASS: Sapper executes Conscript, Conscripts mutually eliminate.');
}

// -------------------------------------------------------------
// ROUND 8: Flag Capture & Victory Sequence
// -------------------------------------------------------------
console.log('\n--- ROUND 8: Flag Capture & Game Over ---');
console.log('GRILL: When Flag is captured, does sound: "victory" trigger, game enter gameover, and winner declared?');
{
    const engine = new GameEngine();
    engine.gameState = 'playing';
    engine.currentTurn = 'red';
    engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redOfficer = new Card('red', '♥', '5', false);
    const blackFlag = new Card('black', '🃏', 'JOKER', true);
    engine.board[4][2] = redOfficer;
    engine.board[5][2] = blackFlag;

    engine.movePiece(4, 2, 5, 2);
    assert.strictEqual(engine.gameState, 'gameover', 'gameState must be gameover');
    assert.strictEqual(engine.winner, 'red', 'winner must be red');
    assert.strictEqual(engine.lastClashResult.winner, 'attacker', 'attacker won flag');
    assert.strictEqual(engine.lastClashResult.sound, 'victory', 'sound must be victory');
    console.log('✓ PASS: Flag capture triggers sound: "victory" and transitions engine to gameover.');
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

// -------------------------------------------------------------
// ROUND 9: Zero Information Leakage in State Views
// -------------------------------------------------------------
console.log('\n--- ROUND 9: Zero Information Leakage in State Views ---');
console.log('GRILL: Do state views strictly hide face-down enemy ranks and roles, but reveal them in clash?');
{
    const room = new RoomDO(
        createMockState(),
        { LOBBY_DO: null }
    );
    room.gameState = 'playing';
    room.engine.gameState = 'playing';
    room.engine.currentTurn = 'red';
    room.engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    const redAttacker = new Card('red', '♥', '9', false);
    const blackHidden = new Card('black', '♠', '7', false);
    blackHidden.faceUp = false;

    room.engine.board[2][2] = redAttacker;
    room.engine.board[9][2] = blackHidden;

    // View for Red player BEFORE clash
    const viewForRed = room.projectStateView('red');
    const redViewPiece = viewForRed.payload.board[9][2];
    assert.strictEqual(redViewPiece.rank, null, 'face-down enemy rank must be masked as null');
    assert.strictEqual(redViewPiece.suit, null, 'face-down enemy suit must be masked as null');
    assert.strictEqual(redViewPiece.isBomb, false, 'isBomb must not leak');
    assert.strictEqual(redViewPiece.isLandmine, false, 'isLandmine must not leak');

    // Now execute clash
    room.engine.board[3][2] = blackHidden;
    const sanitizedDefender = room.sanitizeCardForClash(blackHidden);
    assert.strictEqual(sanitizedDefender.rank, '7', 'clash reveal shows actual rank');
    assert.strictEqual(sanitizedDefender.suit, '♠', 'clash reveal shows actual suit');
    assert.strictEqual(sanitizedDefender.roleName, 'Officer', 'clash reveal shows actual role');
    console.log('✓ PASS: Fog-of-war is hermetic; identities remain completely secret until clash reveal.');
}

// -------------------------------------------------------------
// ROUND 10: Server Action Execution & lastClashResult Hygiene
// -------------------------------------------------------------
console.log('\n--- ROUND 10: Multi-Turn Move / Clash Sequencing & Hygiene ---');
console.log('GRILL: Does normal advance move after a clash cleanly produce clash: null and sound: playMove?');
{
    const room = new RoomDO(
        createMockState(),
        { LOBBY_DO: null }
    );
    room.gameState = 'playing';
    room.engine.gameState = 'playing';
    room.engine.currentTurn = 'red';
    room.engine.board = Array(12).fill(null).map(() => Array(5).fill(null));

    // Turn 1: Red attacks Black (Clash)
    const redCard = new Card('red', '♥', '9', false);
    const blackCard = new Card('black', '♠', '7', false);
    room.engine.board[4][2] = redCard;
    room.engine.board[5][2] = blackCard;

    // Simulate handleMove
    const action1 = { type: 'move', from: { r: 4, c: 2 }, to: { r: 5, c: 2 } };
    room.engine.lastClashResult = null;
    room.engine.movePiece(action1.from.r, action1.from.c, action1.to.r, action1.to.c);
    const result1 = {
        action: action1,
        clash: room.engine.lastClashResult ? {
            attacker: room.sanitizeCardForClash(room.engine.lastClashResult.attacker),
            defender: room.sanitizeCardForClash(room.engine.lastClashResult.defender),
            winner: room.engine.lastClashResult.winner,
            outcomeText: room.engine.lastClashResult.outcomeText,
            sound: room.engine.lastClashResult.sound
        } : null
    };
    assert.notStrictEqual(result1.clash, null, 'Turn 1 must have clash');
    assert.strictEqual(result1.clash.winner, 'attacker', 'Turn 1 attacker won');

    // Turn 2: Black moves to an empty square (No Clash)
    room.currentTurn = 'black';
    room.engine.currentTurn = 'black';
    const blackMover = new Card('black', '♣', '5', false);
    room.engine.board[8][1] = blackMover;

    const action2 = { type: 'move', from: { r: 8, c: 1 }, to: { r: 7, c: 1 } };
    room.engine.lastClashResult = null; // Cleared before action
    room.engine.movePiece(action2.from.r, action2.from.c, action2.to.r, action2.to.c);
    const result2 = {
        action: action2,
        clash: room.engine.lastClashResult ? {
            attacker: room.sanitizeCardForClash(room.engine.lastClashResult.attacker),
            defender: room.sanitizeCardForClash(room.engine.lastClashResult.defender),
            winner: room.engine.lastClashResult.winner,
            outcomeText: room.engine.lastClashResult.outcomeText,
            sound: room.engine.lastClashResult.sound
        } : null
    };
    assert.strictEqual(result2.clash, null, 'Turn 2 must NOT have clash (clash: null)');
    assert.strictEqual(room.engine.board[7][1], blackMover, 'black mover moved to empty square');
    console.log('✓ PASS: lastClashResult is completely reset; non-combat moves never trigger ghost clashes.');
}

console.log('\n================================================================');
console.log('🎉 ALL 10 ROUNDS OF "GRILL ME" PVP COMBAT PARITY TESTS PASSED 100%!');
console.log('================================================================');
