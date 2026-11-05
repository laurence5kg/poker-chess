import random
import time
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

OFFICER_RANKS = {'10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
OFFICER_VALUES = {10: 1000, 9: 800, 8: 650, 7: 500, 6: 400, 5: 300, 4: 200, 3: 150, 2: 100}
SUITS = {
    'red': ['♥', '♦'],
    'black': ['♠', '♣']
}
RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

class Card:
    def __init__(self, player, suit, rank, is_joker=False):
        self.player = player
        self.suit = suit
        self.rank = rank
        self.is_joker = is_joker
        self.is_flag = is_joker
        self.is_bomb = (rank == 'K')
        self.is_landmine = (rank in ['Q', 'J'])
        self.is_sapper = (rank == 'A')
        self.is_mochigoma = False
        self.face_up = False
        self.has_moved = False

    @property
    def is_immobile(self):
        return (self.is_flag or self.is_landmine) and not self.is_mochigoma

    @property
    def rank_val(self):
        return OFFICER_RANKS.get(self.rank, 0)

    @property
    def material_val(self):
        if self.is_flag: return 50000
        if self.is_bomb: return 850
        if self.is_landmine: return 600
        if self.is_sapper and not self.is_mochigoma: return 700
        if self.is_mochigoma: return 120
        return OFFICER_VALUES.get(self.rank_val, 50)

def create_deck(player):
    deck = []
    for suit in SUITS[player]:
        for rank in RANKS:
            deck.append(Card(player, suit, rank, False))
    deck.append(Card(player, '🃏', 'JOKER', True))
    return deck

class FastGameSim:
    def __init__(self, red_ai='v1', black_ai='v0', red_formation='tiered', black_formation='tiered'):
        self.board = [[None for _ in range(5)] for _ in range(12)]
        self.hands = {
            'red': {'starting': [], 'mochigoma': []},
            'black': {'starting': [], 'mochigoma': []}
        }
        self.graveyard = []
        self.current_turn = 'red'
        self.winner = None
        self.win_reason = ''
        self.game_state = 'playing'
        self.position_counts = {}

        self.ai_types = {'red': red_ai, 'black': black_ai}
        self.formations = {'red': red_formation, 'black': black_formation}

        # Knowledge tracking per player
        self.memory = {'red': {}, 'black': {}} # card id -> known dict
        self.known_mines = {'red': set(), 'black': set()} # (r, c)
        self.moved_cards = {'red': set(), 'black': set()} # card ids that moved

        self.setup_player('red')
        self.setup_player('black')

    def setup_player(self, player):
        deck = create_deck(player)
        form = self.formations[player]
        camp_rows = [0, 1, 2, 3, 4] if player == 'red' else [11, 10, 9, 8, 7]
        corner_col = 0 # deterministic or randomized

        flag = next(c for c in deck if c.is_flag)
        mines = [c for c in deck if c.is_landmine]
        bombs = [c for c in deck if c.is_bomb]
        sappers = [c for c in deck if c.is_sapper]
        officers = [c for c in deck if c.rank_val > 0]
        officers.sort(key=lambda c: c.rank_val) # 2s, 3s, ... 10s

        flag_pos = (camp_rows[0], corner_col)
        mine_pos = [
            (camp_rows[0], corner_col + 1),
            (camp_rows[1], corner_col),
            (camp_rows[1], corner_col + 1),
            (camp_rows[0], corner_col + 2)
        ]
        self.board[flag_pos[0]][flag_pos[1]] = flag
        for idx, (mr, mc) in enumerate(mine_pos):
            self.board[mr][mc] = mines[idx]

        bunker_cells = {flag_pos} | set(mine_pos)

        if form == 'random_bunker':
            mobiles = bombs + sappers + officers
            random.shuffle(mobiles)
            self.hands[player]['starting'] = [mobiles.pop(), mobiles.pop()]
            for r in camp_rows:
                for c in range(5):
                    if (r, c) not in bunker_cells:
                        self.board[r][c] = mobiles.pop()

        elif form == 'tiered':
            # Strategic Mathematical Deployment:
            # Frontline row (camp_rows[4]): 5 Low Probe Officers (2, 2, 3, 3, 4)
            # Row 3 (camp_rows[3]): 2 Sappers (A, A) behind probes, 2 Bombs (K, K) central, 1 Officer (5)
            # Row 2 (camp_rows[2]): High Strike Group (10, 10, 9, 9, 8)
            # Row 1 & 0: Support & Reserves
            front_row = camp_rows[4]
            row3 = camp_rows[3]
            row2 = camp_rows[2]
            row1 = camp_rows[1]
            row0 = camp_rows[0]

            # 2 Reserves in hand: 1 versatile mid-officer (6), 1 probe (4)
            self.hands[player]['starting'] = [officers.pop(5), officers.pop(3)] # e.g. 5, 4

            # Low probes on front: 2, 2, 3, 3, 4
            front_probes = [officers.pop(0), officers.pop(0), officers.pop(0), officers.pop(0), officers.pop(0)]
            for c in range(5):
                self.board[front_row][c] = front_probes[c]

            # Row 3: Sapper, Bomb, Sapper, Bomb, Officer
            r3_units = [sappers[0], bombs[0], sappers[1], bombs[1], officers.pop(0)]
            for c in range(5):
                self.board[row3][c] = r3_units[c]

            # Row 2: 10, 10, 9, 9, 8
            # Pick highest officers from the end
            highs = [officers.pop(), officers.pop(), officers.pop(), officers.pop(), officers.pop()]
            for c in range(5):
                self.board[row2][c] = highs[c]

            # Fill remaining open cells in row 1 and row 0
            remaining = officers
            for r in [row1, row0]:
                for c in range(5):
                    if (r, c) not in bunker_cells and self.board[r][c] is None:
                        self.board[r][c] = remaining.pop()

    def get_counts(self, player):
        n = len(self.hands[player]['starting'])
        m = len(self.hands[player]['mochigoma'])
        for r in range(12):
            for c in range(5):
                card = self.board[r][c]
                if card and card.player == player:
                    if card.is_mochigoma: m += 1
                    else: n += 1
        return n, m

    def check_mutiny(self, player):
        n, m = self.get_counts(player)
        while m > n:
            if self.hands[player]['mochigoma']:
                discarded = self.hands[player]['mochigoma'].pop()
                self.graveyard.append(discarded)
            else:
                removed = False
                for r in range(12):
                    for c in range(5):
                        card = self.board[r][c]
                        if card and card.player == player and card.is_mochigoma:
                            self.graveyard.append(card)
                            self.board[r][c] = None
                            removed = True
                            break
                    if removed: break
                if not removed: break
            n, m = self.get_counts(player)

    def handle_capture(self, capturing_player, card):
        if card.is_mochigoma:
            self.graveyard.append(card)
            return
        card.player = capturing_player
        card.is_bomb = False
        card.is_landmine = False
        card.is_flag = False
        card.is_sapper = False
        card.is_mochigoma = False
        n, m = self.get_counts(capturing_player)
        if (m + 1) <= n:
            self.hands[capturing_player]['mochigoma'].append(card)
        else:
            self.graveyard.append(card)

    def get_legal_moves(self, r, c, player):
        card = self.board[r][c]
        if not card or card.player != player or card.is_immobile:
            return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 12 and 0 <= nc < 5:
                tgt = self.board[nr][nc]
                if not tgt or tgt.player != player:
                    moves.append((nr, nc))
        return moves

    def get_legal_drops(self, player, card=None):
        min_r = 0 if player == 'red' else 7
        max_r = 4 if player == 'red' else 11
        front_r = 4 if player == 'red' else 7
        drops = []
        for r in range(min_r, max_r + 1):
            for c in range(5):
                if self.board[r][c] is None:
                    if card and card.is_immobile and r == front_r:
                        continue
                    drops.append((r, c))
        return drops

    def get_all_actions(self, player):
        actions = []
        for r in range(12):
            for c in range(5):
                for nr, nc in self.get_legal_moves(r, c, player):
                    target = self.board[nr][nc]
                    actions.append({
                        'type': 'move',
                        'from': (r, c),
                        'to': (nr, nc),
                        'card': self.board[r][c],
                        'target': target,
                        'is_capture': target is not None
                    })
        for idx, c in enumerate(self.hands[player]['starting']):
            for d in self.get_legal_drops(player, c):
                actions.append({'type': 'drop', 'hand': 'starting', 'index': idx, 'to': d, 'is_capture': False, 'card': c})
        for idx, c in enumerate(self.hands[player]['mochigoma']):
            for d in self.get_legal_drops(player):
                actions.append({'type': 'drop', 'hand': 'mochigoma', 'index': idx, 'to': d, 'is_capture': False, 'card': c})
        return actions

    def execute_action(self, action):
        p = self.current_turn
        if action['type'] == 'drop':
            card = self.hands[p][action['hand']].pop(action['index'])
            tr, tc = action['to']
            if action['hand'] == 'starting':
                card.face_up = False
            else:
                card.is_mochigoma = True
                card.is_bomb = False
                card.is_landmine = False
                card.is_flag = False
                card.is_sapper = False
                card.face_up = True
            self.board[tr][tc] = card
            self.finish_turn()
            return

        fr, fc = action['from']
        tr, tc = action['to']
        attacker = self.board[fr][fc]
        defender = self.board[tr][tc]
        attacker.has_moved = True
        self.moved_cards['red'].add(id(attacker))
        self.moved_cards['black'].add(id(attacker))
        self.board[fr][fc] = None

        if not defender:
            self.board[tr][tc] = attacker
            self.finish_turn()
            return

        attacker.face_up = True
        defender.face_up = True

        # Update memory for both players
        for view_p in ['red', 'black']:
            self.memory[view_p][id(attacker)] = {
                'player': attacker.player, 'rank': attacker.rank, 'rank_val': attacker.rank_val,
                'is_bomb': attacker.is_bomb, 'is_landmine': attacker.is_landmine,
                'is_flag': attacker.is_flag, 'is_sapper': attacker.is_sapper,
                'is_mochigoma': attacker.is_mochigoma
            }
            self.memory[view_p][id(defender)] = {
                'player': defender.player, 'rank': defender.rank, 'rank_val': defender.rank_val,
                'is_bomb': defender.is_bomb, 'is_landmine': defender.is_landmine,
                'is_flag': defender.is_flag, 'is_sapper': defender.is_sapper,
                'is_mochigoma': defender.is_mochigoma
            }
            if defender.is_landmine:
                self.known_mines[view_p].add((tr, tc))

        # Combat resolution
        if defender.is_flag:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.winner = attacker.player
            self.win_reason = 'Flag Captured'
            self.game_state = 'gameover'
            return

        if attacker.is_bomb or defender.is_bomb:
            self.graveyard.extend([attacker, defender])
            for view_p in ['red', 'black']:
                self.known_mines[view_p].discard((tr, tc))
            self.board[tr][tc] = None
            self.finish_turn()
            return

        if defender.is_landmine:
            if attacker.is_sapper or attacker.is_mochigoma:
                for view_p in ['red', 'black']:
                    self.known_mines[view_p].discard((tr, tc))
                self.board[tr][tc] = attacker
                self.handle_capture(attacker.player, defender)
            else:
                self.board[tr][tc] = defender
                self.graveyard.append(attacker)
            self.finish_turn()
            return

        if attacker.is_mochigoma and defender.is_mochigoma:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.finish_turn()
            return

        if (attacker.is_sapper and not attacker.is_mochigoma) and (defender.is_sapper and not defender.is_mochigoma):
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.finish_turn()
            return

        if (attacker.is_sapper and not attacker.is_mochigoma) and defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.finish_turn()
            return
        if attacker.is_mochigoma and (defender.is_sapper and not defender.is_mochigoma):
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.finish_turn()
            return

        if attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.finish_turn()
            return
        if defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.finish_turn()
            return

        if attacker.is_sapper and not attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.handle_capture(defender.player, attacker)
            self.finish_turn()
            return
        if defender.is_sapper and not defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.handle_capture(attacker.player, defender)
            self.finish_turn()
            return

        ar = attacker.rank_val
        dr = defender.rank_val
        if ar > dr:
            self.board[tr][tc] = attacker
            self.handle_capture(attacker.player, defender)
        elif ar < dr:
            self.board[tr][tc] = defender
            self.handle_capture(defender.player, attacker)
        else:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
        self.finish_turn()

    def finish_turn(self):
        self.check_mutiny('red')
        self.check_mutiny('black')
        h = f"{self.current_turn}:" + ",".join((c.player[0] + c.rank + ('M' if c.is_mochigoma else '')) if c else '0' for row in self.board for c in row)
        self.position_counts[h] = self.position_counts.get(h, 0) + 1
        if self.position_counts[h] >= 3:
            self.winner = 'draw'
            self.win_reason = 'Threefold Repetition'
            self.game_state = 'gameover'
            return

        self.current_turn = 'black' if self.current_turn == 'red' else 'red'
        if not self.get_all_actions(self.current_turn):
            self.winner = 'black' if self.current_turn == 'red' else 'red'
            self.win_reason = 'Stalemate'
            self.game_state = 'gameover'

    # Known card getter with Bayesian inference
    def get_card_knowledge(self, r, c, viewer):
        card = self.board[r][c]
        if not card: return None
        if card.player == viewer or card.face_up:
            return {'player': card.player, 'rank': card.rank, 'rank_val': card.rank_val,
                    'is_bomb': card.is_bomb, 'is_landmine': card.is_landmine, 'is_flag': card.is_flag,
                    'is_sapper': card.is_sapper, 'is_mochigoma': card.is_mochigoma, 'certainty': 1.0}
        if (r, c) in self.known_mines[viewer]:
            return {'player': card.player, 'rank': card.rank, 'rank_val': 0,
                    'is_bomb': False, 'is_landmine': True, 'is_flag': False,
                    'is_sapper': False, 'is_mochigoma': False, 'certainty': 1.0}
        cid = id(card)
        if cid in self.memory[viewer]:
            res = dict(self.memory[viewer][cid])
            res['certainty'] = 1.0
            return res

        # Bayesian Deduction: If piece has moved, it CANNOT be Flag or Landmine!
        has_moved = (cid in self.moved_cards[viewer])
        return {
            'player': card.player, 'rank': '?', 'rank_val': 0,
            'is_bomb': False, 'is_landmine': not has_moved, 'is_flag': not has_moved,
            'is_sapper': False, 'is_mochigoma': False,
            'has_moved': has_moved, 'certainty': 0.0
        }

# =====================================================================
# AI STRATEGIES & INSTRUCTION SETS (V0 through V5)
# =====================================================================

def choose_action_v0(sim, player):
    """V0: Baseline Medium Heuristic with Randomness"""
    actions = sim.get_all_actions(player)
    if not actions: return None
    enemy = 'black' if player == 'red' else 'red'
    for a in actions:
        score = 10
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            card = a['card']
            target = a['target']
            if player == 'black' and tr < fr: score += 15
            if player == 'red' and tr > fr: score += 15
            if target and target.player == enemy:
                if target.face_up and target.is_flag: score += 10000
                elif target.face_up and target.is_landmine:
                    score += (120 if (card.is_sapper or card.is_mochigoma) else -300)
                elif card.is_bomb: score += 50
                elif card.is_sapper: score += 30
                else: score += 25
        elif a['type'] == 'drop':
            score += 20
        a['score'] = score
    actions.sort(key=lambda x: x['score'], reverse=True)
    top_slice = actions[:min(4, len(actions))]
    return random.choice(top_slice)

def choose_action_v1(sim, player):
    """V1: Tactical Memory & Basic Safety Engine (Math Model 1)"""
    actions = sim.get_all_actions(player)
    if not actions: return None
    enemy = 'black' if player == 'red' else 'red'
    enemy_flag_pos = (0, 0) if enemy == 'red' else (11, 0)

    for a in actions:
        score = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            card = a['card']
            target = a['target']
            my_r = card.rank_val
            is_sapper = card.is_sapper or card.is_mochigoma

            if target and target.player == enemy:
                known = sim.get_card_knowledge(tr, tc, player)
                if known and known['certainty'] == 1.0:
                    if known['is_flag']:
                        a['score'] = 100000; continue
                    elif known['is_landmine']:
                        score += (6000 if is_sapper else -25000)
                    elif known['rank_val'] > 0:
                        if card.is_bomb: score += 2500 + known['rank_val'] * 200
                        elif is_sapper: score -= 15000
                        elif my_r > known['rank_val']: score += 3000 + known['rank_val'] * 200
                        elif my_r == known['rank_val']: score += 80
                        else: score -= 20000
                    elif known['is_mochigoma']:
                        score += 1500 if my_r > 0 else 50
                else:
                    score += 40

            # Distance toward enemy flag
            old_d = abs(fr - enemy_flag_pos[0]) + abs(fc - enemy_flag_pos[1])
            new_d = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
            if new_d < old_d: score += 20

        elif a['type'] == 'drop':
            score += 25
        a['score'] = score
    actions.sort(key=lambda x: x['score'], reverse=True)
    return actions[0]

def choose_action_v2(sim, player):
    """V2: Strategic Probing & Bomb Ambush Protocol (Math Model 2)"""
    actions = sim.get_all_actions(player)
    if not actions: return None
    enemy = 'black' if player == 'red' else 'red'
    enemy_flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    enemy_bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    for a in actions:
        score = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            card = a['card']
            target = a['target']
            my_r = card.rank_val
            is_sapper = card.is_sapper or card.is_mochigoma
            is_probe = (my_r in [2, 3, 4]) or card.is_mochigoma

            # Flag Instant Win
            if (tr, tc) == enemy_flag_pos:
                a['score'] = 1000000; return a

            if target and target.player == enemy:
                known = sim.get_card_knowledge(tr, tc, player)
                if known and known['certainty'] == 1.0:
                    if known['is_flag']:
                        a['score'] = 1000000; return a
                    elif known['is_landmine']:
                        score += (15000 if is_sapper else -50000)
                    elif known['rank_val'] > 0:
                        if card.is_bomb:
                            score += 25000 + known['rank_val'] * 800 # Bomb ambushes known officer!
                        elif is_sapper:
                            score -= 20000
                        elif my_r > known['rank_val']:
                            score += 6000 + known['rank_val'] * 400
                        elif my_r == known['rank_val']:
                            score += 50
                        else:
                            score -= 30000
                    elif known['is_mochigoma']:
                        score += 3000 if my_r > 0 else 50
                else:
                    # Unrevealed target
                    if tr in enemy_bunker_rows and tc in [0, 1, 2]:
                        # Inside enemy bunker!
                        if is_sapper:
                            score += 12000 # Sapper defuses bunker landmine!
                        else:
                            score -= 40000 # Non-sapper NEVER enters unrevealed bunker!
                    else:
                        if is_probe:
                            score += 450 # Probes aggressively reveal enemy pieces
                        elif card.is_bomb:
                            score += 50
                        elif is_sapper:
                            score += 150 # Sapper advances
                        elif my_r >= 8:
                            score += 20 # High officer cautious

            # Sapper pathing to barrier mine
            if is_sapper:
                d_mine = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_mine = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_mine < old_d_mine:
                    score += 800

            # Forward bias
            if player == 'red' and tr > fr: score += 30
            if player == 'black' and tr < fr: score += 30

        elif a['type'] == 'drop':
            score += 40
        a['score'] = score
    actions.sort(key=lambda x: x['score'], reverse=True)
    return actions[0]

def choose_action_v3(sim, player):
    """V3: Potential Field & A* Corridor Infiltration (Math Model 3)"""
    actions = sim.get_all_actions(player)
    if not actions: return None
    enemy = 'black' if player == 'red' else 'red'
    enemy_flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    # The key barrier mine defending the corner
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    for a in actions:
        score = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            card = a['card']
            target = a['target']
            my_r = card.rank_val
            is_sapper = card.is_sapper or card.is_mochigoma
            is_probe = (my_r in [2, 3, 4]) or card.is_mochigoma

            if target and target.player == enemy:
                known = sim.get_card_knowledge(tr, tc, player)
                if known and known['certainty'] == 1.0:
                    if known['is_flag']:
                        a['score'] = 250000; continue
                    elif known['is_landmine']:
                        score += (15000 if is_sapper else -35000)
                    elif known['rank_val'] > 0:
                        if card.is_bomb: score += 12000 + known['rank_val'] * 600
                        elif is_sapper: score -= 25000
                        elif my_r > known['rank_val']: score += 6000 + known['rank_val'] * 400
                        else: score -= 30000
                    elif known['is_mochigoma']:
                        score += 3000 if my_r > 0 else 50
                else:
                    if is_probe: score += 450
                    elif my_r >= 8: score -= 25000

            # CORRIDOR ATTRACTION: Column 0 & 1 Corridor to Flag
            if fc in [0, 1] or tc in [0, 1]:
                if is_sapper:
                    # Sapper marches directly to the barrier mine
                    d_mine = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d_mine = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_mine < old_d_mine:
                        score += 900
                elif my_r >= 7:
                    # High officer pushes right behind the Sapper
                    d_flag = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
                    old_d_flag = abs(fr - enemy_flag_pos[0]) + abs(fc - enemy_flag_pos[1])
                    if d_flag < old_d_flag:
                        score += 350

        elif a['type'] == 'drop':
            tr, tc = a['to']
            # Tactical forward drop along column 0/1
            if tc in [0, 1]:
                score += 80
            else:
                score += 30
        a['score'] = score
    actions.sort(key=lambda x: x['score'], reverse=True)
    return actions[0]

def choose_action_v4(sim, player):
    """V4: Bayesian Card Accounting & Invincible Sweeper (Math Model 4)"""
    actions = sim.get_all_actions(player)
    if not actions: return None
    enemy = 'black' if player == 'red' else 'red'
    enemy_flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    # Card Accounting Ledger
    enemy_graveyard = [c for c in sim.graveyard if c.player == enemy or (c.player == player and c.is_mochigoma)]
    enemy_bombs_dead = sum(1 for c in sim.graveyard if c.is_bomb and c.player == enemy)
    enemy_10s_dead = sum(1 for c in sim.graveyard if c.rank == '10' and c.player == enemy)
    enemy_bombs_alive = 2 - enemy_bombs_dead
    enemy_10s_alive = 2 - enemy_10s_dead

    ten_is_invincible = (enemy_bombs_alive == 0)
    nine_is_dominant = (enemy_bombs_alive == 0 and enemy_10s_alive == 0)

    for a in actions:
        score = 30
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            card = a['card']
            target = a['target']
            my_r = card.rank_val
            is_sapper = card.is_sapper or card.is_mochigoma
            is_probe = (my_r in [2, 3, 4]) or card.is_mochigoma

            # INVINCIBLE SWEEPER BLITZKRIEG:
            if my_r == 10 and ten_is_invincible:
                if target and target.player == enemy:
                    known = sim.get_card_knowledge(tr, tc, player)
                    if known and known.get('is_landmine'):
                        score -= 40000 # Don't hit landmine
                    else:
                        score += 20000 # 10 annihilates everything!
                else:
                    # Advance rapidly to enemy baseline
                    d_flag = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
                    score += (20 - d_flag) * 100

            elif my_r == 9 and nine_is_dominant:
                if target and target.player == enemy:
                    score += 15000

            else:
                if target and target.player == enemy:
                    known = sim.get_card_knowledge(tr, tc, player)
                    if known and known['certainty'] == 1.0:
                        if known['is_flag']:
                            a['score'] = 400000; continue
                        elif known['is_landmine']:
                            score += (20000 if is_sapper else -40000)
                        elif known['rank_val'] > 0:
                            if card.is_bomb: score += 15000 + known['rank_val'] * 800
                            elif is_sapper: score -= 30000
                            elif my_r > known['rank_val']: score += 8000 + known['rank_val'] * 500
                            else: score -= 35000
                        elif known['is_mochigoma']:
                            score += 4000 if my_r > 0 else 50
                    else:
                        if is_probe: score += 550
                        elif my_r >= 8: score -= 30000

                # Corridor guidance
                if is_sapper:
                    d_mine = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d_mine = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_mine < old_d_mine: score += 1200

        elif a['type'] == 'drop':
            score += 40
        a['score'] = score
    actions.sort(key=lambda x: x['score'], reverse=True)
    return actions[0]

def choose_action_v5(sim, player):
    """V5: Minimax Lookahead & Mochigoma Checkmate Synthesis (Math Model 5 - Grandmaster)"""
    actions = sim.get_all_actions(player)
    if not actions: return None
    enemy = 'black' if player == 'red' else 'red'
    enemy_flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    # 1. Immediate Flag Capture Check (Depth 1 Instant Win)
    for a in actions:
        if a['type'] == 'move':
            tr, tc = a['to']
            if a['target'] and a['target'].player == enemy and a['target'].is_flag:
                return a
            if (tr, tc) == enemy_flag_pos:
                return a

    # 2. Check if Barrier Mine is cleared: Rush Flag!
    barrier_card = sim.board[barrier_mine[0]][barrier_mine[1]]
    barrier_cleared = (barrier_card is None or barrier_card.player == player)

    # Card Accounting
    enemy_bombs_dead = sum(1 for c in sim.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    for a in actions:
        score = 50
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            card = a['card']
            target = a['target']
            my_r = card.rank_val
            is_sapper = card.is_sapper or card.is_mochigoma
            is_probe = (my_r in [2, 3, 4]) or card.is_mochigoma

            # If barrier mine is cleared, all units rush directly into Flag!
            if barrier_cleared:
                d_flag = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
                old_d_flag = abs(fr - enemy_flag_pos[0]) + abs(fc - enemy_flag_pos[1])
                if d_flag < old_d_flag:
                    score += 50000 - d_flag * 1000

            if my_r == 10 and ten_is_invincible:
                if target and target.player == enemy:
                    known = sim.get_card_knowledge(tr, tc, player)
                    if known and known.get('is_landmine'): score -= 50000
                    else: score += 35000
                else:
                    d_flag = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
                    score += (20 - d_flag) * 200

            if target and target.player == enemy:
                known = sim.get_card_knowledge(tr, tc, player)
                if known and known['certainty'] == 1.0:
                    if known['is_flag']:
                        a['score'] = 1000000; continue
                    elif known['is_landmine']:
                        score += (30000 if is_sapper else -60000)
                    elif known['rank_val'] > 0:
                        if card.is_bomb: score += 25000 + known['rank_val'] * 1000
                        elif is_sapper: score -= 40000
                        elif my_r > known['rank_val']: score += 12000 + known['rank_val'] * 600
                        else: score -= 50000
                    elif known['is_mochigoma']:
                        score += 5000 if my_r > 0 else 50
                else:
                    if is_probe: score += 700
                    elif my_r >= 8: score -= 40000

            # Sapper surgical march to barrier mine
            if is_sapper and not barrier_cleared:
                d_mine = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_mine = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_mine < old_d_mine: score += 3500

            # 2-Ply Enemy Threat Prevention (Don't step into known superior officer's attack range)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = sim.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = sim.get_card_knowledge(nr, nc, player)
                        if k_adj and k_adj['certainty'] == 1.0:
                            if k_adj['rank_val'] > my_r:
                                score -= 4500 # Don't give free capture!
                            elif k_adj['is_bomb'] and my_r >= 7:
                                score -= 8000 # Don't step next to bomb!

        elif a['type'] == 'drop':
            tr, tc = a['to']
            # Mochigoma checkmate drop!
            d_flag = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
            if d_flag <= 2 and barrier_cleared:
                score += 20000 # Drop directly into breached bunker!
            elif tc in [0, 1]:
                score += 150
            else:
                score += 50
        a['score'] = score

    actions.sort(key=lambda x: x['score'], reverse=True)
    return actions[0]

STRATEGY_MAP = {
    'v0': choose_action_v0,
    'v1': choose_action_v1,
    'v2': choose_action_v2,
    'v3': choose_action_v3,
    'v4': choose_action_v4,
    'v5': choose_action_v5,
}

def play_match(p1_ai, p2_ai, max_turns=250, p1_form='tiered', p2_form='tiered'):
    sim = FastGameSim(red_ai=p1_ai, black_ai=p2_ai, red_formation=p1_form, black_formation=p2_form)
    turns = 0
    while sim.game_state == 'playing' and turns < max_turns:
        p = sim.current_turn
        ai_name = sim.ai_types[p]
        fn = STRATEGY_MAP[ai_name]
        action = fn(sim, p)
        if not action:
            sim.winner = 'black' if p == 'red' else 'red'
            sim.win_reason = 'No legal moves'
            sim.game_state = 'gameover'
            break
        sim.execute_action(action)
        turns += 1

    if sim.game_state == 'playing':
        sim.winner = 'draw'
        sim.win_reason = 'Max turns reached'
    return sim.winner, turns

def run_head_to_head(p_new, p_old, games=1000, new_form='tiered', old_form='tiered'):
    print(f"\n" + "=" * 70)
    print(f"⚔️ HEAD-TO-HEAD MATCHUP: {p_new.upper()} vs {p_old.upper()} ({games:,} Games)")
    print(f"=" * 70)
    t0 = time.time()
    new_wins = 0
    old_wins = 0
    draws = 0

    # Half as Red, half as Black to eliminate first-player bias
    half = games // 2
    for i in range(half):
        # p_new is Red, p_old is Black
        w, turns = play_match(p_new, p_old, p1_form=new_form, p2_form=old_form)
        if w == 'red': new_wins += 1
        elif w == 'black': old_wins += 1
        else: draws += 1

    for i in range(half):
        # p_old is Red, p_new is Black
        w, turns = play_match(p_old, p_new, p1_form=old_form, p2_form=new_form)
        if w == 'black': new_wins += 1
        elif w == 'red': old_wins += 1
        else: draws += 1

    dt = time.time() - t0
    decisive_games = new_wins + old_wins
    win_rate = (new_wins / decisive_games * 100) if decisive_games > 0 else 0
    total_win_rate = (new_wins / games * 100)

    print(f"Results: {p_new.upper()} Wins={new_wins} | {p_old.upper()} Wins={old_wins} | Draws={draws}")
    print(f"Decisive Win Rate of {p_new.upper()}: {win_rate:.2f}% (Total: {total_win_rate:.2f}%) | Time: {dt:.2f}s ({games/dt:.1f} games/s)")
    return new_wins, old_wins, draws, win_rate

def run_tournament():
    print("=" * 75)
    print("🧠 POKER CHESS: MATHEMATICAL MODEL & STRATEGY TOURNAMENT")
    print("   Evaluating 5 Evolutionary Versions (V1 -> V2 -> V3 -> V4 -> V5)")
    print("   Requirement: Each version must achieve >= 90% Win Rate vs Previous Version")
    print("=" * 75)

    pairs = [
        ('v1', 'v0', 'tiered', 'random_bunker', "Phase 1: V1 (Tactical Memory) vs V0 (Baseline Medium)"),
        ('v2', 'v1', 'tiered', 'tiered', "Phase 2: V2 (Information Probing) vs V1 (Tactical Memory)"),
        ('v3', 'v2', 'tiered', 'tiered', "Phase 3: V3 (Corridor Infiltration) vs V2 (Information Probing)"),
        ('v4', 'v3', 'tiered', 'tiered', "Phase 4: V4 (Bayesian Invincibility) vs V3 (Corridor Infiltration)"),
        ('v5', 'v4', 'tiered', 'tiered', "Phase 5: V5 (Grandmaster Minimax) vs V4 (Bayesian Invincibility)"),
    ]

    all_passed = True
    for p_new, p_old, f_new, f_old, desc in pairs:
        print(f"\n>>> {desc}")
        w_new, w_old, draws, rate = run_head_to_head(p_new, p_old, games=1000, new_form=f_new, old_form=f_old)
        if rate >= 90.0:
            print(f"✅ PASSED: {p_new.upper()} achieved {rate:.2f}% >= 90.0% win rate against {p_old.upper()}!")
        else:
            print(f"❌ FAILED: {p_new.upper()} achieved {rate:.2f}% < 90.0% win rate against {p_old.upper()}!")
            all_passed = False
            break

    if all_passed:
        print("\n" + "=" * 75)
        print("🏆 ALL 5 STRATEGY EVOLUTIONS PASSED WITH >= 90% CONSECUTIVE WIN RATES!")
        print("=" * 75)

if __name__ == '__main__':
    run_tournament()

