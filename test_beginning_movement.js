import { GameEngine } from './game.js';

console.log('====================================================');
console.log('🧪 TESTING BEGINNING MOVEMENT IN PVE & PVP (10 ROUNDS)');
console.log('====================================================');

// Round 1: PvE as Red - Launch Battle
console.log('\n[Round 1] PvE Red: Game launch state & immediate legal moves...');
const pveRed = new GameEngine();
pveRed.resetForNewGame({ mode: 'pve', humanSide: 'red' });
console.log('  GameState:', pveRed.gameState, '| CurrentTurn:', pveRed.currentTurn);
if (pveRed.gameState !== 'playing') throw new Error('PvE Red should start in playing state!');
if (pveRed.currentTurn !== 'red') throw new Error('Red should move first!');

const redFrontlineMoves = [];
for (let c = 0; c < 5; c++) {
    const card = pveRed.board[4][c];
    if (!card) throw new Error(`Expected frontline card at (4, ${c})`);
    const moves = pveRed.getLegalMoves(4, c);
    redFrontlineMoves.push({ col: c, rank: card.rank, suit: card.suit, moves });
}
console.log('  Red Frontline (Row 4) legal moves:', redFrontlineMoves.map(m => `Col ${m.col} (${m.rank}${m.suit}) -> ${m.moves.length} moves`));
if (redFrontlineMoves.some(m => m.moves.length === 0)) throw new Error('All frontline cards should have legal moves!');
console.log('  ✅ Round 1 Passed: PvE Red has 5 immediately movable frontline units!');

// Round 2: PvE as Black - Launch Battle
console.log('\n[Round 2] PvE Black: Game launch state & immediate legal moves...');
const pveBlack = new GameEngine();
pveBlack.resetForNewGame({ mode: 'pve', humanSide: 'black' });
console.log('  GameState:', pveBlack.gameState, '| CurrentTurn:', pveBlack.currentTurn);
if (pveBlack.gameState !== 'playing') throw new Error('PvE Black should start in playing state!');
const blackMoves = [];
for (let c = 0; c < 5; c++) {
    const card = pveBlack.board[7][c];
    if (!card) throw new Error(`Expected frontline card at (7, ${c})`);
    const moves = pveBlack.getLegalMoves(7, c);
    blackMoves.push({ col: c, rank: card.rank, suit: card.suit, moves });
}
console.log('  Black Frontline (Row 7) legal moves:', blackMoves.map(m => `Col ${m.col} (${m.rank}${m.suit}) -> ${m.moves.length} moves`));
if (blackMoves.some(m => m.moves.length === 0)) throw new Error('All Black frontline cards should have legal moves!');
console.log('  ✅ Round 2 Passed: PvE Black has 5 immediately movable frontline units!');

// Round 3: Local PvP 1v1 - Launch Battle
console.log('\n[Round 3] Local PvP 1v1: Immediate playability for both sides...');
const pvp = new GameEngine();
pvp.resetForNewGame({ mode: 'pvp', humanSide: 'red' });
console.log('  GameState:', pvp.gameState, '| CurrentTurn:', pvp.currentTurn);
if (pvp.gameState !== 'playing') throw new Error('Local PvP should start in playing state!');
if (pvp.currentTurn !== 'red') throw new Error('Red should move first in PvP!');

// Red executes first move
const m1 = pvp.getLegalMoves(4, 0)[0];
console.log('  Red moves (4, 0) ->', m1);
pvp.movePiece(4, 0, m1.r, m1.c);
console.log('  After Red move: currentTurn =', pvp.currentTurn);
if (pvp.currentTurn !== 'black') throw new Error('Turn should pass to black!');

// Black executes first move
const m2 = pvp.getLegalMoves(7, 0)[0];
console.log('  Black moves (7, 0) ->', m2);
pvp.movePiece(7, 0, m2.r, m2.c);
console.log('  After Black move: currentTurn =', pvp.currentTurn);
if (pvp.currentTurn !== 'red') throw new Error('Turn should pass to red!');
console.log('  ✅ Round 3 Passed: Local PvP immediately playable with alternating turns!');

// Round 4: Inner Units Blocked Verification (Junqi Invariant)
console.log('\n[Round 4] Inner Unit Blocked Invariant: Rows 0..3 have 0 legal moves on turn 1...');
let blockedCount = 0;
for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 5; c++) {
        const moves = pveRed.getLegalMoves(r, c);
        if (moves.length === 0) blockedCount++;
    }
}
console.log(`  Blocked inner units count: ${blockedCount}/20`);
if (blockedCount !== 20) throw new Error(`Expected exactly 20 blocked units in rows 0..3, got ${blockedCount}`);
console.log('  ✅ Round 4 Passed: Strict physical blocking invariant holds for all 20 inner units.');

// Round 5: Path Clearing Verification (Advancing frontline unblocks row 3)
console.log('\n[Round 5] Path Clearing: Moving frontline unit unblocks the unit directly behind it...');
const testGame = new GameEngine();
testGame.resetForNewGame({ mode: 'pvp' });
const behindUnitMovesBefore = testGame.getLegalMoves(3, 2);
console.log('  Unit at (3, 2) legal moves before frontline advances:', behindUnitMovesBefore.length);
if (behindUnitMovesBefore.length !== 0) throw new Error('Unit at (3, 2) must be blocked initially');

// Advance frontline unit at (4, 2) to (5, 2)
testGame.movePiece(4, 2, 5, 2);
// Switch turn back to red for testing
testGame.currentTurn = 'red';
const behindUnitMovesAfter = testGame.getLegalMoves(3, 2);
console.log('  Unit at (3, 2) legal moves AFTER frontline advances to (5, 2):', behindUnitMovesAfter);
if (behindUnitMovesAfter.length !== 1 || behindUnitMovesAfter[0].r !== 4 || behindUnitMovesAfter[0].c !== 2) {
    throw new Error('Unit at (3, 2) should now be able to advance into the vacated (4, 2)!');
}
console.log('  ✅ Round 5 Passed: Vacating frontline tile successfully unblocks the supporting unit behind it!');

// Round 6: Reserve Integrity Check
console.log('\n[Round 6] Reserve Integrity Check...');
console.log('  Red starting reserves count:', testGame.hands.red.startingReserves.length);
console.log('  Black starting reserves count:', testGame.hands.black.startingReserves.length);
if (testGame.hands.red.startingReserves.length !== 2 || testGame.hands.black.startingReserves.length !== 2) {
    throw new Error('Each player must start with exactly 2 reserves!');
}
console.log('  ✅ Round 6 Passed: Secret Reserves correctly initialized to 2 cards per player.');

// Round 7: Anti-Mutiny Caps Initialization
console.log('\n[Round 7] Anti-Mutiny Caps Initialization...');
const redCounts = testGame.getCounts('red');
const blackCounts = testGame.getCounts('black');
console.log('  Red Army:', redCounts, '| Black Army:', blackCounts);
if (redCounts.native !== 27 || redCounts.mochigoma !== 0) throw new Error('Red starting army must have 27 native (25 camp + 2 reserve) and 0 mochigoma');
if (blackCounts.native !== 27 || blackCounts.mochigoma !== 0) throw new Error('Black starting army must have 27 native (25 camp + 2 reserve) and 0 mochigoma');
console.log('  ✅ Round 7 Passed: Mutiny counts strictly 27 native / 0 conscript.');

// Round 8: Online Mode Setup Phase Parity
console.log('\n[Round 8] Online Mode Setup Phase: Auto-fills formation ready for 1-click confirm...');
const onlineGame = new GameEngine();
onlineGame.resetForNewGame({ mode: 'online', humanSide: 'red' });
console.log('  Online GameState:', onlineGame.gameState, '| SetupPlayer:', onlineGame.setupPlayer);
if (onlineGame.gameState !== 'setup') throw new Error('Online mode must start in setup state for secret layout confirmation');
const redValidation = onlineGame.validateSetup('red');
const blackValidation = onlineGame.validateSetup('black');
console.log('  Red Validation:', redValidation.valid, '| Placed:', redValidation.placedCount, '/ 25 | Reserves:', redValidation.reserveCount, '/ 2');
console.log('  Black Validation:', blackValidation.valid, '| Placed:', blackValidation.placedCount, '/ 25 | Reserves:', blackValidation.reserveCount, '/ 2');
if (!redValidation.valid || !blackValidation.valid) throw new Error('Both formations must be pre-validated and valid on setup start!');
console.log('  ✅ Round 8 Passed: Online setup pre-deploys 100% valid formations ready for 1-click Battle confirmation!');

// Round 9: 4-Player 2v2 Game Start Parity
console.log('\n[Round 9] 4-Player 2v2 Mode Game Start...');
const fourP = new GameEngine();
fourP.resetForNewGame({ mode: '4p_2v2', playerCount: 4, fourPlayerMode: '2v2' });
console.log('  4P GameState:', fourP.gameState, '| CurrentTurn:', fourP.currentTurn);
let fourPMovable = 0;
for (let r = 0; r < 15; r++) {
    for (let c = 0; c < 15; c++) {
        const card = fourP.board[r][c];
        if (card && card.player === 'a') {
            const moves = fourP.getLegalMoves(r, c);
            if (moves.length > 0) fourPMovable++;
        }
    }
}
console.log('  Player A movable frontline units:', fourPMovable);
if (fourPMovable === 0) throw new Error('Player A in 4P mode must have legal moves on turn 1!');
console.log('  ✅ Round 9 Passed: 4-Player mode verified with movable frontline units.');

// Round 10: Bot Turn Execution in PvE
console.log('\n[Round 10] Bot Turn Execution in PvE...');
const pveBotTest = new GameEngine();
pveBotTest.resetForNewGame({ mode: 'pve', humanSide: 'red' });
// Red moves frontline
const redMove = pveBotTest.getLegalMoves(4, 1)[0];
pveBotTest.movePiece(4, 1, redMove.r, redMove.c);
console.log('  Red moved to (5, 1). Turn now:', pveBotTest.currentTurn);
if (pveBotTest.currentTurn !== 'black') throw new Error('Turn must pass to bot');
// Bot executes turn
pveBotTest.runBotTurn();
console.log('  After Bot runBotTurn(): currentTurn =', pveBotTest.currentTurn);
if (pveBotTest.currentTurn !== 'red') throw new Error('Turn must pass back to human after bot move');
console.log('  Move log text:', pveBotTest.moveLog[0].text);
console.log('  ✅ Round 10 Passed: Bot executes turn and returns play to human seamlessly!');

console.log('\n🎉 ALL 10 ROUNDS OF "GRILL ME" VERIFICATION PASSED WITH 100% SUCCESS!');
