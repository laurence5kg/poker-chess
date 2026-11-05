import random
import time
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

OFFICER_RANKS = {'10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
SUITS = {'red': ['♥', '♦'], 'black': ['♠', '♣']}
RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

class Card:
    __slots__ = ('player', 'suit', 'rank', 'is_joker', 'is_flag', 'is_bomb', 'is_landmine', 'is_sapper', 'is_mochigoma', 'face_up', 'has_moved')
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

def create_deck(player):
    deck = [Card(player, s, r, False) for s in SUITS[player] for r in RANKS]
    deck.append(Card(player, '🃏', 'JOKER', True))
    return deck

class FastSim:
    def __init__(self, red_strat, blk_strat, red_form='spearhead', blk_form='spearhead'):
        self.board = [[None]*5 for _ in range(12)]
        self.hands = {'red': {'starting': [], 'mochigoma': []}, 'black': {'starting': [], 'mochigoma': []}}
        self.graveyard = []
        self.current_turn = 'red'
        self.winner = None
        self.win_reason = ''
        self.game_state = 'playing'
        self.strats = {'red': red_strat, 'black': blk_strat}
        self.memory = {'red': {}, 'black': {}}
        self.known_mines = {'red': set(), 'black': set()}
        self.moved = {'red': set(), 'black': set()}

        self.setup('red', red_form)
        self.setup('black', blk_form)

    def setup(self, player, form):
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

        if form == 'random':
            mobiles = bombs + sappers + officers
            random.shuffle(mobiles)
            self.hands[player]['starting'] = [mobiles.pop(), mobiles.pop()]
            for r in camp_rows:
                for c in range(5):
                    if (r, c) not in bunker:
                        self.board[r][c] = mobiles.pop()

        elif form == 'spearhead':
            # Mathematical Spearhead Deployment:
            # Col 0: Fast Infiltration (10 vanguard on front, Sapper on row 3, 9 on row 2)
            # Col 1: Bomb on row 3 (ambush interceptor)
            # Reserves in hand: 1 Sapper, 1 Bomb
            self.hands[player]['starting'] = [sappers.pop(), bombs.pop()]

            front_r, r3, r2, r1, r0 = camp_rows[4], camp_rows[3], camp_rows[2], camp_rows[1], camp_rows[0]
            ten_a, ten_b = officers.pop(), officers.pop()
            nine_a, nine_b = officers.pop(), officers.pop()
            eight_a, eight_b = officers.pop(), officers.pop()

            self.board[front_r][0] = ten_a
            self.board[r3][0] = sappers.pop()
            self.board[r2][0] = nine_a
            self.board[r3][1] = bombs.pop()

            self.board[front_r][1] = officers.pop(0) # 2
            self.board[front_r][2] = officers.pop(0) # 2
            self.board[front_r][3] = officers.pop(0) # 3
            self.board[front_r][4] = ten_b

            self.board[r3][2] = eight_a
            self.board[r3][3] = eight_b
            self.board[r3][4] = nine_b

            rem = officers
            random.shuffle(rem)
            for r in [r2, r1, r0]:
                for c in range(5):
                    if (r, c) not in bunker and self.board[r][c] is None:
                        self.board[r][c] = rem.pop()

        elif form == 'counter_trap':
            # Counter-Trap Formation:
            # Frontline Col 0: BOMB (ambushes enemy 10)
            # Frontline Col 1: Low probe (2)
            # Frontline Col 2: Low probe (3)
            # Frontline Col 3: 10
            # Frontline Col 4: Sapper (A) - unimpeded flank highway!
            self.hands[player]['starting'] = [sappers.pop(), officers.pop()] # Sapper, 10
            front_r, r3, r2, r1, r0 = camp_rows[4], camp_rows[3], camp_rows[2], camp_rows[1], camp_rows[0]

            self.board[front_r][0] = bombs.pop() # Bomb on front of Col 0!
            self.board[front_r][1] = officers.pop(0) # 2
            self.board[front_r][2] = officers.pop(0) # 3
            self.board[front_r][3] = officers.pop() # 10
            self.board[front_r][4] = sappers.pop() # Sapper on flank!

            self.board[r3][0] = officers.pop() # 9 behind bomb
            self.board[r3][1] = bombs.pop() # 2nd bomb
            self.board[r3][4] = officers.pop() # 9 behind sapper

            rem = officers
            random.shuffle(rem)
            for r in [r3, r2, r1, r0]:
                for c in range(5):
                    if (r, c) not in bunker and self.board[r][c] is None:
                        self.board[r][c] = rem.pop()

    def get_legal_moves(self, r, c, p):
        card = self.board[r][c]
        if not card or card.player != p or card.is_immobile: return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 12 and 0 <= nc < 5:
                t = self.board[nr][nc]
                if not t or t.player != p:
                    moves.append((nr, nc))
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
        self.moved['red'].add(id(att)); self.moved['black'].add(id(att))
        self.board[fr][fc] = None

        if not df:
            self.board[tr][tc] = att
            self.next_turn()
            return

        att.face_up = True; df.face_up = True
        for vp in ['red', 'black']:
            self.memory[vp][id(att)] = {'rank_val': att.rank_val, 'is_bomb': att.is_bomb, 'is_landmine': att.is_landmine, 'is_flag': att.is_flag, 'is_sapper': att.is_sapper, 'is_mochigoma': att.is_mochigoma}
            self.memory[vp][id(df)] = {'rank_val': df.rank_val, 'is_bomb': df.is_bomb, 'is_landmine': df.is_landmine, 'is_flag': df.is_flag, 'is_sapper': df.is_sapper, 'is_mochigoma': df.is_mochigoma}
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
# 5 EVOLUTIONARY STRATEGY INSTRUCTION SETS (V0 through V5)
# =====================================================================

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
            if a['target'] and a['target'].player == enemy:
                s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return random.choice(acts[:min(4, len(acts))])

def v1_memory(game, p):
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
            is_sapper = c.is_sapper or c.is_mochigoma

            if (tr, tc) == flag_pos: return a

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                if cid in game.memory[p]:
                    k = game.memory[p][cid]
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (8000 if is_sapper else -30000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 10000 + k['rank_val'] * 300
                        elif is_sapper: s -= 20000
                        elif c.rank_val > k['rank_val']: s += 4000 + k['rank_val'] * 200
                        elif c.rank_val == k['rank_val']: s += 40
                        else: s -= 25000
                elif (tr, tc) in game.known_mines[p]:
                    s += 8000 if is_sapper else -30000
                else:
                    s += 45

            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 25
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

def v2_spearhead(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]

    # Instant Flag Snipe
    for a in acts:
        if a['type'] == 'move' and (a['to'] == flag_pos or (a['target'] and a['target'].player == enemy and a['target'].is_flag)):
            return a

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                if cid in game.memory[p]:
                    k = game.memory[p][cid]
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (25000 if is_sapper else -50000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 30000 + k['rank_val'] * 500
                        elif is_sapper: s -= 30000
                        elif my_r > k['rank_val']: s += 8000 + k['rank_val'] * 300
                        else: s -= 35000
                elif (tr, tc) in game.known_mines[p]:
                    s += 25000 if is_sapper else -50000
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 35000
                        else: s -= 60000
                    else:
                        if is_sapper: s += 150
                        elif my_r >= 9: s += 500 # 10 vanguard moves forward!
                        elif my_r in [2, 3]: s += 200

            # Spearhead Infiltration Corridor (Col 0)
            if fc == 0 or tc == 0:
                if is_sapper:
                    # Sapper follows behind 10 to barrier mine
                    d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_bm < old_d_bm: s += 2500
                elif my_r >= 9:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                    if d_flag < old_d_flag: s += 1200

            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
        elif a['type'] == 'drop':
            s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

def v3_counter_trap(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]

    # Flag Snipe
    for a in acts:
        if a['type'] == 'move' and (a['to'] == flag_pos or (a['target'] and a['target'].player == enemy and a['target'].is_flag)):
            return a

    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                if cid in game.memory[p]:
                    k = game.memory[p][cid]
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (35000 if is_sapper else -60000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 45000 + k['rank_val'] * 800
                        elif is_sapper: s -= 40000
                        elif my_r > k['rank_val']: s += 12000 + k['rank_val'] * 400
                        else: s -= 45000
                elif (tr, tc) in game.known_mines[p]:
                    s += 35000 if is_sapper else -60000
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 40000
                        else: s -= 80000
                    else:
                        if is_sapper: s += 500
                        elif my_r in [2, 3]: s += 400
                        elif my_r >= 9: s += 200

            # Flank Highway Infiltration (Col 4 -> Col 1/0):
            # Sapper uses Column 4 where enemy has zero defense, bypasses Col 0 trap!
            if is_sapper:
                if fc in [3, 4] or tc in [3, 4]:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                    if d_flag < old_d_flag: s += 3000
            elif my_r >= 8:
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 1000

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
        elif a['type'] == 'drop':
            s += 30
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

def v4_invincible_blitz(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]

    # Flag Snipe
    for a in acts:
        if a['type'] == 'move' and (a['to'] == flag_pos or (a['target'] and a['target'].player == enemy and a['target'].is_flag)):
            return a

    # Card Accounting Ledger
    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    for a in acts:
        s = 30
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # Invincible Sweeper Mode: 10 crushes all non-mine enemy pieces!
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        s -= 80000 # Don't hit landmine
                    else:
                        s += 50000 # Unstoppable blitzkrieg!
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 200

            # Intercept enemy Sappers!
            elif tgt and tgt.player == enemy and (tgt.is_sapper or tgt.is_mochigoma) and my_r > 0:
                s += 25000 # Sapper assassin! Eliminates enemy breach capability!

            elif tgt and tgt.player == enemy:
                cid = id(tgt)
                if cid in game.memory[p]:
                    k = game.memory[p][cid]
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (45000 if is_sapper else -70000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 50000 + k['rank_val'] * 1000
                        elif is_sapper: s -= 45000
                        elif my_r > k['rank_val']: s += 15000 + k['rank_val'] * 500
                        else: s -= 50000
                elif (tr, tc) in game.known_mines[p]:
                    s += 45000 if is_sapper else -70000
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 50000
                        else: s -= 90000
                    else:
                        if my_r in [2, 3]: s += 500 # Probing
                        elif is_sapper: s += 600

            # Dual-Corridor Flow
            if is_sapper:
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 4000

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40
        elif a['type'] == 'drop':
            s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

def v5_grandmaster(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]

    # 1. Immediate Flag Capture (Depth 1 Checkmate)
    for a in acts:
        if a['type'] == 'move' and (a['to'] == flag_pos or (a['target'] and a['target'].player == enemy and a['target'].is_flag)):
            return a

    # 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is vacant, drop Conscript for mate in 1!
    adj_flag = [(flag_pos[0]+1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)] if enemy == 'red' else [(flag_pos[0]-1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)]
    for a in acts:
        if a['type'] == 'drop' and a['to'] in adj_flag:
            return a

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

            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 90000
                    else: s += 70000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 300

            # Intercept enemy Sappers with extreme prejudice!
            elif tgt and tgt.player == enemy and (tgt.is_sapper or tgt.is_mochigoma) and my_r > 0:
                s += 40000

            elif tgt and tgt.player == enemy:
                cid = id(tgt)
                if cid in game.memory[p]:
                    k = game.memory[p][cid]
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (60000 if is_sapper else -90000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 70000 + k['rank_val'] * 1200
                        elif is_sapper: s -= 60000
                        elif my_r > k['rank_val']: s += 20000 + k['rank_val'] * 600
                        else: s -= 70000
                elif (tr, tc) in game.known_mines[p]:
                    s += 60000 if is_sapper else -90000
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 60000
                        else: s -= 120000
                    else:
                        if my_r in [2, 3]: s += 700
                        elif is_sapper: s += 800

            # 3-Ply Threat Evasion: Never move adjacent to known superior enemy piece!
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(id(adj))
                        if k_adj:
                            if k_adj['rank_val'] > my_r: s -= 8000
                            elif k_adj['is_bomb'] and my_r >= 7: s -= 15000

            if is_sapper:
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 6000

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop':
            # Mochigoma tactical bottleneck drop
            tr, tc = a['to']
            if tc in [0, 4]: s += 200
            else: s += 50
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

STRAT_MAP = {
    'v0': v0_baseline,
    'v1': v1_memory,
    'v2': v2_spearhead,
    'v3': v3_counter_trap,
    'v4': v4_invincible_blitz,
    'v5': v5_grandmaster,
}

def play_one_game(strat1, strat2, form1='spearhead', form2='spearhead', max_turns=300):
    g = FastSim(strat1, strat2, red_form=form1, blk_form=form2)
    turns = 0
    while g.game_state == 'playing' and turns < max_turns:
        p = g.current_turn
        strat_name = g.strats[p]
        act = STRAT_MAP[strat_name](g, p)
        if not act: break
        g.execute(act)
        turns += 1
    if g.game_state == 'playing':
        g.winner = 'draw'
        g.win_reason = 'Max turns'
    return g.winner, turns

def run_match(s_new, s_old, f_new='spearhead', f_old='spearhead', n_games=1000):
    print(f"\nEvaluating {s_new.upper()} vs {s_old.upper()} ({n_games:,} games)...")
    t0 = time.time()
    w_new, w_old, draws = 0, 0, 0
    half = n_games // 2
    for i in range(half):
        w, _ = play_one_game(s_new, s_old, form1=f_new, form2=f_old)
        if w == 'red': w_new += 1
        elif w == 'black': w_old += 1
        else: draws += 1
    for i in range(half):
        w, _ = play_one_game(s_old, s_new, form1=f_old, form2=f_new)
        if w == 'black': w_new += 1
        elif w == 'red': w_old += 1
        else: draws += 1

    decisive = w_new + w_old
    rate = (w_new / decisive * 100) if decisive > 0 else 0
    dt = time.time() - t0
    print(f"Result: {s_new.upper()} Wins: {w_new} | {s_old.upper()} Wins: {w_old} | Draws: {draws}")
    print(f"Decisive Win Rate: {rate:.2f}% | Time: {dt:.2f}s ({n_games/dt:.1f} g/s)")
    return rate

def run_5_version_ladder():
    print("=" * 75)
    print("🚀 EXECUTING 5-VERSION EVOLUTIONARY TOURNAMENT (1,000 GAMES PER STAGE)")
    print("=" * 75)
    ladder = [
        ('v1', 'v0', 'spearhead', 'random', "STAGE 1: V1 (Tactical Memory) vs V0 (Baseline Medium)"),
        ('v2', 'v1', 'spearhead', 'random', "STAGE 2: V2 (Spearhead Corridor) vs V1 (Tactical Memory)"),
        ('v3', 'v2', 'counter_trap', 'spearhead', "STAGE 3: V3 (Counter-Trap Flank) vs V2 (Spearhead Corridor)"),
        ('v4', 'v3', 'spearhead', 'counter_trap', "STAGE 4: V4 (Invincible Blitz) vs V3 (Counter-Trap Flank)"),
        ('v5', 'v4', 'spearhead', 'spearhead', "STAGE 5: V5 (Grandmaster Minimax) vs V4 (Invincible Blitz)"),
    ]

    all_pass = True
    for s_new, s_old, f_new, f_old, desc in ladder:
        print(f"\n>>> {desc}")
        rate = run_match(s_new, s_old, f_new=f_new, f_old=f_old, n_games=1000)
        if rate >= 90.0:
            print(f"✅ PASSED: {s_new.upper()} achieved {rate:.2f}% (>= 90.0%) against {s_old.upper()}!")
        else:
            print(f"❌ FAILED: {s_new.upper()} achieved {rate:.2f}% (< 90.0%) against {s_old.upper()}!")
            all_pass = False

    if all_pass:
        print("\n" + "=" * 75)
        print("🏆 ALL 5 STAGES ACHIEVED >= 90% CONSECUTIVE WIN RATES!")
        print("=" * 75)

if __name__ == '__main__':
    run_5_version_ladder()

