import re
import os

game_path = os.path.join(os.path.dirname(__file__), 'game.js')
with open(game_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Locate getBestActionLow and runBotTurn
start_marker = "    getBestActionLow(actions, botSide, enemySide) {"
end_marker = "    runBotTurn() {"

start_pos = content.find(start_marker)
end_pos = content.find(end_marker)

assert start_pos != -1, "start_marker not found"
assert end_pos != -1, "end_marker not found"

new_code = '''    getBestActionLow(actions, botSide, enemySide) {
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
'''

new_content = content[:start_pos] + new_code + '\n' + content[end_pos:]

with open(game_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully upgraded game.js with Low=M50, Medium=M100, High=M200!")
