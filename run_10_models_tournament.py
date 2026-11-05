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
SUITS = {'red': ['♥', '♦'], 'black': ['♠', '♣']}
RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

class Card:
    __slots__ = ('id', 'player', 'suit', 'rank', 'is_joker', 'is_flag', 'is_bomb', 'is_landmine', 'is_sapper', 'is_mochigoma', 'face_up', 'has_moved')
    _id_counter = 0

    def __init__(self, player, suit, rank, is_joker=False):
        Card._id_counter += 1
        self.id = Card._id_counter
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

def create_deck(player):
    deck = [Card(player, s, r, False) for s in SUITS[player] for r in RANKS]
    deck.append(Card(player, '🃏', 'JOKER', True))
    return deck

class FastMatchEngine:
    def __init__(self, red_strat, blk_strat, red_tier=1, blk_tier=0):
        self.board = [[None]*5 for _ in range(12)]
        self.hands = {'red': {'starting': [], 'mochigoma': []}, 'black': {'starting': [], 'mochigoma': []}}
        self.graveyard = []
        self.current_turn = 'red'
        self.winner = None
        self.win_reason = ''
        self.game_state = 'playing'
        self.strats = {'red': red_strat, 'black': blk_strat}
        # Explicit Card Memory: memory[viewer][card.id] = {rank_val, is_bomb, is_landmine, is_flag, is_sapper}
        self.memory = {'red': {}, 'black': {}}
        self.known_mines = {'red': set(), 'black': set()}

        self.setup('red', red_tier)
        self.setup('black', blk_tier)

    def setup(self, player, tier):
        deck = create_deck(player)
        camp_rows = [0, 1, 2, 3, 4] if player == 'red' else [11, 10, 9, 8, 7]
        flag = next(c for c in deck if c.is_flag)
        mines = [c for c in deck if c.is_landmine]
        bombs = [c for c in deck if c.is_bomb]
        sappers = [c for c in deck if c.is_sapper]
        officers = sorted([c for c in deck if c.rank_val > 0], key=lambda c: c.rank_val)

        flag_pos = (camp_rows[0], 0)
        mine_pos = [(camp_rows[0], 1), (camp_rows[1], 0), (camp_rows[1], 1), (camp_rows[0], 2)]
        self.board[flag_pos[0]][flag_pos[1]] = flag
        for i, (mr, mc) in enumerate(mine_pos):
            self.board[mr][mc] = mines[i]
        bunker = {flag_pos} | set(mine_pos)

        if tier == 0: # Naive random placement
            mobiles = bombs + sappers + officers
            random.shuffle(mobiles)
            self.hands[player]['starting'] = [mobiles.pop(), mobiles.pop()]
            for r in camp_rows:
                for c in range(5):
                    if (r, c) not in bunker:
                        self.board[r][c] = mobiles.pop()
        else: # Mathematical Optimal Tiered Assignment
            self.hands[player]['starting'] = [bombs.pop(), officers.pop(4)]
            front_r, r3, r2 = camp_rows[4], camp_rows[3], camp_rows[2]
            # Frontline: Low probes 2, 2, 3, 3, 4
            for c in range(5): self.board[front_r][c] = officers.pop(0)
            # Row 3: Bomb on column 0, Sapper on col 1 & 3, Officers on col 2 & 4
            self.board[r3][0] = bombs.pop()
            self.board[r3][1] = sappers.pop()
            self.board[r3][2] = officers.pop()
            self.board[r3][3] = sappers.pop()
            self.board[r3][4] = officers.pop()
            # Row 2: Heavy Strike Group 10, 10, 9, 9, 8
            for c in range(5): self.board[r2][c] = officers.pop()
            # Support rows
            for r in [camp_rows[1], camp_rows[0]]:
                for c in range(5):
                    if (r, c) not in bunker and self.board[r][c] is None:
                        self.board[r][c] = officers.pop()

    def get_legal_moves(self, r, c, p):
        card = self.board[r][c]
        if not card or card.player != p or card.is_immobile: return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 12 and 0 <= nc < 5:
                t = self.board[nr][nc]
                if not t or t.player != p: moves.append((nr, nc))
        return moves

    def get_actions(self, p):
        actions = []
        for r in range(12):
            for c in range(5):
                for nr, nc in self.get_legal_moves(r, c, p):
                    t = self.board[nr][nc]
                    actions.append({'type': 'move', 'from': (r, c), 'to': (nr, nc), 'card': self.board[r][c], 'target': t})
        min_r = 0 if p == 'red' else 7
        max_r = 4 if p == 'red' else 11
        for h_type in ['starting', 'mochigoma']:
            for idx, c in enumerate(self.hands[p][h_type]):
                for r in range(min_r, max_r + 1):
                    for col in range(5):
                        if self.board[r][col] is None:
                            actions.append({'type': 'drop', 'hand': h_type, 'index': idx, 'to': (r, col), 'target': None, 'card': c})
        return actions

    def execute(self, a):
        p = self.current_turn
        if a['type'] == 'drop':
            card = self.hands[p][a['hand']].pop(a['index'])
            tr, tc = a['to']
            if a['hand'] == 'starting':
                card.face_up = False
            else:
                card.is_mochigoma = True
                card.is_bomb = False; card.is_landmine = False; card.is_flag = False; card.is_sapper = False; card.face_up = True
            self.board[tr][tc] = card
            self.next_turn()
            return

        fr, fc = a['from']
        tr, tc = a['to']
        att = self.board[fr][fc]
        df = self.board[tr][tc]
        att.has_moved = True
        self.board[fr][fc] = None

        if not df:
            self.board[tr][tc] = att
            self.next_turn()
            return

        att.face_up = True; df.face_up = True
        for vp in ['red', 'black']:
            self.memory[vp][att.id] = {'rank_val': att.rank_val, 'is_bomb': att.is_bomb, 'is_landmine': att.is_landmine, 'is_flag': att.is_flag, 'is_sapper': att.is_sapper, 'is_mochigoma': att.is_mochigoma}
            self.memory[vp][df.id] = {'rank_val': df.rank_val, 'is_bomb': df.is_bomb, 'is_landmine': df.is_landmine, 'is_flag': df.is_flag, 'is_sapper': df.is_sapper, 'is_mochigoma': df.is_mochigoma}
            if df.is_landmine: self.known_mines[vp].add((tr, tc))

        if df.is_flag:
            self.board[tr][tc] = att
            self.graveyard.append(df)
            self.winner = att.player
            self.win_reason = 'Flag Captured'
            self.game_state = 'gameover'
            return

        if att.is_bomb or df.is_bomb:
            self.graveyard.extend([att, df])
            for vp in ['red', 'black']: self.known_mines[vp].discard((tr, tc))
            self.board[tr][tc] = None
            self.next_turn()
            return

        if df.is_landmine:
            if att.is_sapper or att.is_mochigoma:
                for vp in ['red', 'black']: self.known_mines[vp].discard((tr, tc))
                self.board[tr][tc] = att
                self.capture(att.player, df)
            else:
                self.board[tr][tc] = df
                self.graveyard.append(att)
            self.next_turn()
            return

        if att.is_mochigoma or df.is_mochigoma:
            if att.is_mochigoma and df.is_mochigoma:
                self.graveyard.extend([att, df]); self.board[tr][tc] = None
            elif att.is_mochigoma:
                self.board[tr][tc] = df; self.graveyard.append(att)
            else:
                self.board[tr][tc] = att; self.graveyard.append(df)
            self.next_turn()
            return

        if att.is_sapper or df.is_sapper:
            if att.is_sapper and df.is_sapper:
                self.graveyard.extend([att, df]); self.board[tr][tc] = None
            elif att.is_sapper:
                self.board[tr][tc] = df; self.capture(df.player, att)
            else:
                self.board[tr][tc] = att; self.capture(att.player, df)
            self.next_turn()
            return

        ar, dr = att.rank_val, df.rank_val
        if ar > dr:
            self.board[tr][tc] = att; self.capture(att.player, df)
        elif ar < dr:
            self.board[tr][tc] = df; self.capture(df.player, att)
        else:
            self.graveyard.extend([att, df]); self.board[tr][tc] = None
        self.next_turn()

    def capture(self, capturing_p, card):
        card.player = capturing_p; card.is_bomb = False; card.is_landmine = False; card.is_flag = False; card.is_sapper = False; card.is_mochigoma = False
        n = sum(1 for r in self.board for c in r if c and c.player == capturing_p and not c.is_mochigoma)
        m = sum(1 for r in self.board for c in r if c and c.player == capturing_p and c.is_mochigoma) + len(self.hands[capturing_p]['mochigoma'])
        if m + 1 <= n:
            self.hands[capturing_p]['mochigoma'].append(card)
        else:
            self.graveyard.append(card)

    def next_turn(self):
        self.current_turn = 'black' if self.current_turn == 'red' else 'red'
        acts = self.get_actions(self.current_turn)
        if not acts:
            self.winner = 'black' if self.current_turn == 'red' else 'red'
            self.win_reason = 'Stalemate'
            self.game_state = 'gameover'

# =====================================================================
# THE 10 MATHEMATICAL MODELS & 10 STRATEGY INSTRUCTION SETS
# =====================================================================

# V0: Baseline Random with Forward Bias
def v0_baseline(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    for a in acts:
        s = 10
        if a['type'] == 'move':
            fr, tr = a['from'][0], a['to'][0]
            if p == 'red' and tr > fr: s += 15
            if p == 'black' and tr < fr: s += 15
            if a['target'] and a['target'].player == enemy: s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return random.choice(acts[:min(4, len(acts))])

# V1: Model 1 - Memory Invariant & Absolute Blunder Veto
def v1_memory_veto(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)

    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if (tr, tc) == flag_pos: return a
            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 50000
                        else: s = -9999999 # ABSOLUTE VETO
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 60000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999 # Sapper never attacks known officer!
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999 # ABSOLUTE VETO: Smaller card NEVER attacks bigger!
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 50000
                    else: s = -9999999
                else:
                    s += 40

            if p == 'red' and tr > fr: s += 25
            if p == 'black' and tr < fr: s += 25
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V2: Model 2 - Threat Zone Adjacency & 1-Ply Horizon Safety
def v2_threat_zone(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if (tr, tc) == flag_pos: return a
            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 60000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 70000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 45000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 60000
                    else: s = -9999999
                else:
                    s += 40

            # Threat Zone Avoidance: Do NOT move adjacent to known bigger enemy officers!
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000 # Threat penalty

            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V3: Model 3 - Sapper Preservation & Mine Hunter Vector
def v3_sapper_preserve(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if (tr, tc) == flag_pos: return a
            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 80000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 80000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 50000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 80000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000 # Sapper preservation
                    elif my_r in [2, 3]: s += 1000
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            # Sapper pathing to barrier mine
            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 30000

            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
        elif a['type'] == 'drop':
            s += 25
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V4: Model 4 - Doorway Clearance & Flow Dynamics
def v4_doorway_clear(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)

    for a in acts:
        s = 30
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if (tr, tc) == flag_pos: return a
            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 90000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 90000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 55000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 90000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000
                    elif my_r in [2, 3]: s += 1500
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 35000

            # Doorway Clearance: Step aside so sapper can defuse!
            if fr == doorway and not is_sapper:
                if tc != 0: s += 40000
                else: s -= 40000

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
        elif a['type'] == 'drop':
            s += 30
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V5: Model 5 - Defcon 1 Homeland Defense
def v5_homeland_defcon1(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # Instant Flag Capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # Defcon 1: Intercept any intruder in our camp!
    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a

    for a in acts:
        s = 35
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 150000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 100000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 100000 + k['rank_val'] * 1500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 60000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 100000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 40000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 45000
                else: s -= 45000

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40
        elif a['type'] == 'drop':
            s += 35
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V6: Model 6 - Tactical Drop-Block Defense
def v6_drop_blockade(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        # Move intercept
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a
        # Tactical Drop Blockade: Drop heavy piece adjacent to intruder
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    for a in acts:
        s = 40
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 160000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 110000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 110000 + k['rank_val'] * 1500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 65000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 110000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000
                    elif my_r in [2, 3]: s += 2500
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 45000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 45000
                else: s -= 45000

            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45
        elif a['type'] == 'drop':
            tr, tc = a['to']
            if p == 'red' and tr == 4: s += 150
            elif p == 'black' and tr == 7: s += 150
            else: s += 30
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V7: Model 7 - Sapper Hunter-Killer Protocol
def v7_hunter_killer(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    # Sapper Hunter-Killer: Find enemy Sapper on board
    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    for a in acts:
        s = 45
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 170000

            # Intercept and eliminate enemy Sapper
            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 100000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 120000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 120000 + k['rank_val'] * 1500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 70000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 120000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000
                    elif my_r in [2, 3]: s += 2500
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 45000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop':
            tr, tc = a['to']
            if p == 'red' and tr == 4: s += 200
            elif p == 'black' and tr == 7: s += 200
            else: s += 30
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V8: Model 8 - Invincible Sweeper Protocol
def v8_invincible_sweep(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    for a in acts:
        s = 50
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 180000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 110000

            # Invincible Sweeper
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 180000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 800

            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 130000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 130000 + k['rank_val'] * 1500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 75000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 130000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000
                    elif my_r in [2, 3]: s += 2500
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 50000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop':
            tr, tc = a['to']
            if p == 'red' and tr == 4: s += 250
            elif p == 'black' and tr == 7: s += 250
            else: s += 40
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V9: Model 9 - Dual-Axis Flank Pincer Protocol
def v9_flank_pincer(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    for a in acts:
        s = 50
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 190000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 120000

            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 900

            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 140000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 140000 + k['rank_val'] * 1500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 80000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 140000
                    else: s = -9999999
                else:
                    if is_sapper: s -= 30000
                    elif my_r in [2, 3]: s += 2500
                    else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 50000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            # Flank Pincer Push along Column 4
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 300

            if p == 'red' and tr > fr: s += 55
            if p == 'black' and tr < fr: s += 55
        elif a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                s += 400
            elif tc in [0, 4]:
                s += 300
            else:
                s += 50
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V10: Model 10 - Grandmaster Hyper-Equilibrium & Mochigoma Checkmate Oracle
def v10_grandmaster_oracle(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Instant Flag Capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is empty, drop Conscript for mate in 1!
    adj_flag = [(flag_pos[0]+1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)] if enemy == 'red' else [(flag_pos[0]-1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)]
    for a in acts:
        if a['type'] == 'drop' and a['to'] in adj_flag:
            return a

    # 3. Defcon 1 Homeland Defense
    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    # 4. Sapper Hunter-Killer
    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    enemy_officers = [c for r in game.board for c in r if c and c.player == enemy and c.rank_val > 0]
    sweep_mode = (len(enemy_officers) <= 4)

    for a in acts:
        s = 50
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 200000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 120000

            # Invincible Sweeper
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 1000

            elif sweep_mode and my_r >= 7:
                if tgt and tgt.player == enemy:
                    s += 150000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 500

            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 160000
                        else: s = -9999999 # Strict Veto
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 170000 + k['rank_val'] * 2000
                        elif is_sapper: s = -9999999 # Sapper never attacks known officer!
                        elif my_r > k['rank_val']: s += 80000 + k['rank_val'] * 800
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999 # Strict Veto: Smaller NEVER attacks bigger!
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 160000
                    else: s = -9999999
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 140000
                        else: s = -9999999
                    else:
                        if my_r in [2, 3]: s += 3000
                        elif is_sapper: s = -30000 # Sapper preservation
                        elif my_r >= 8: s += 200

            # 3-Ply Threat Evasion
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj:
                            if k_adj.get('rank_val', 0) > my_r: s -= 80000
                            elif k_adj.get('is_bomb') and my_r >= 7: s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 50000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            # Heavy officer escort ahead of Sapper
            if fc == 0 and tc == 0 and my_r >= 8:
                d_bm = abs(tr - barrier_mine[0])
                old_d_bm = abs(fr - barrier_mine[0])
                if d_bm < old_d_bm and d_bm >= 2:
                    s += 40000

            # Flank push
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 300

            if p == 'red' and tr > fr: s += 60
            if p == 'black' and tr < fr: s += 60

        elif a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                s += 800
            elif tc in [0, 4]:
                s += 500
            else:
                s += 200
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

STRAT_REGISTRY = {
    'v0_baseline': v0_baseline,
    'v1_memory_veto': v1_memory_veto,
    'v2_threat_zone': v2_threat_zone,
    'v3_sapper_preserve': v3_sapper_preserve,
    'v4_doorway_clear': v4_doorway_clear,
    'v5_homeland_defcon1': v5_homeland_defcon1,
    'v6_drop_blockade': v6_drop_blockade,
    'v7_hunter_killer': v7_hunter_killer,
    'v8_invincible_sweep': v8_invincible_sweep,
    'v9_flank_pincer': v9_flank_pincer,
    'v10_grandmaster_oracle': v10_grandmaster_oracle,
}

def play_match(strat1, strat2, tier1=1, tier2=0, max_turns=300):
    g = FastMatchEngine(strat1, strat2, red_tier=tier1, blk_tier=tier2)
    turns = 0
    while g.game_state == 'playing' and turns < max_turns:
        p = g.current_turn
        s_name = g.strats[p]
        act = STRAT_REGISTRY[s_name](g, p)
        if not act: break
        g.execute(act)
        turns += 1
    if g.game_state == 'playing':
        g.winner = 'draw'
        g.win_reason = 'Max turns'
    return g.winner, turns

def run_tournament_stage(s_new, s_old, t_new=1, t_old=1, games=1000):
    t0 = time.time()
    w_new, w_old, draws = 0, 0, 0
    half = games // 2
    for _ in range(half):
        w, _ = play_match(s_new, s_old, tier1=t_new, tier2=t_old)
        if w == 'red': w_new += 1
        elif w == 'black': w_old += 1
        else: draws += 1
    for _ in range(half):
        w, _ = play_match(s_old, s_new, tier1=t_old, tier2=t_new)
        if w == 'black': w_new += 1
        elif w == 'red': w_old += 1
        else: draws += 1
    dec = w_new + w_old
    rate = (w_new / dec * 100) if dec > 0 else 0
    dt = time.time() - t0
    return w_new, w_old, draws, rate, dt

def main():
    print("=" * 85)
    print("🏆 POKER CHESS: 10-MATHEMATICAL-MODEL & 10-VERSION TOURNAMENT")
    print("   Target: At Least 1,000 Games Per Evolutionary Stage (>= 95% Win Rate Required)")
    print("=" * 85)

    stages = [
        ("STAGE 1: M1 (Memory Veto V1) vs Baseline (V0)", 'v1_memory_veto', 'v0_baseline', 1, 0),
        ("STAGE 2: M2 (Threat Zone V2) vs M1 (Memory Veto V1)", 'v2_threat_zone', 'v1_memory_veto', 1, 1),
        ("STAGE 3: M3 (Sapper Preserve V3) vs M2 (Threat Zone V2)", 'v3_sapper_preserve', 'v2_threat_zone', 1, 1),
        ("STAGE 4: M4 (Doorway Clear V4) vs M3 (Sapper Preserve V3)", 'v4_doorway_clear', 'v3_sapper_preserve', 1, 1),
        ("STAGE 5: M5 (Defcon 1 Homeland V5) vs M4 (Doorway Clear V4)", 'v5_homeland_defcon1', 'v4_doorway_clear', 1, 1),
        ("STAGE 6: M6 (Drop Blockade V6) vs M5 (Defcon 1 Homeland V5)", 'v6_drop_blockade', 'v5_homeland_defcon1', 1, 1),
        ("STAGE 7: M7 (Hunter-Killer V7) vs M6 (Drop Blockade V6)", 'v7_hunter_killer', 'v6_drop_blockade', 1, 1),
        ("STAGE 8: M8 (Invincible Sweep V8) vs M7 (Hunter-Killer V7)", 'v8_invincible_sweep', 'v7_hunter_killer', 1, 1),
        ("STAGE 9: M9 (Flank Pincer V9) vs M8 (Invincible Sweep V8)", 'v9_flank_pincer', 'v8_invincible_sweep', 1, 1),
        ("STAGE 10: M10 (Grandmaster Oracle V10) vs M9 (Flank Pincer V9)", 'v10_grandmaster_oracle', 'v9_flank_pincer', 1, 1),
    ]

    all_passed = True
    for title, s_new, s_old, t_new, t_old in stages:
        print(f"\n▶ {title} ...", flush=True)
        w_new, w_old, draws, rate, dt = run_tournament_stage(s_new, s_old, t_new, t_old, games=1000)
        status = "✅ PASSED" if rate >= 95.0 else "⚠️ CALIBRATING"
        if rate < 95.0: all_passed = False
        print(f"   {status}: {s_new.upper()} Wins={w_new} | {s_old.upper()} Wins={w_old} | Draws={draws}", flush=True)
        print(f"   Decisive Win Rate: {rate:.2f}% | Time: {dt:.2f}s ({1000/dt:.1f} games/s)", flush=True)

    print("\n" + "=" * 85)
    if all_passed:
        print("🎉 ALL 10 STAGES COMPLETED WITH >= 95% WIN RATE ACROSS 10,000 GAMES!")
    else:
        print("⚠️ Some stages require parameter tuning to reach >= 95%.")
    print("=" * 85)

if __name__ == '__main__':
    main()
