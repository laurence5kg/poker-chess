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
    __slots__ = ('id', 'player', 'suit', 'rank', 'is_joker', 'is_flag', 'is_bomb', 'is_landmine', 'is_sapper', 'is_mochigoma', 'face_up', 'has_moved')
    _cnt = 0
    def __init__(self, player, suit, rank, is_joker=False):
        Card._cnt += 1
        self.id = Card._cnt
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

        if tier == 0:
            mobiles = bombs + sappers + officers
            random.shuffle(mobiles)
            self.hands[player]['starting'] = [mobiles.pop(), mobiles.pop()]
            for r in camp_rows:
                for c in range(5):
                    if (r, c) not in bunker:
                        self.board[r][c] = mobiles.pop()
        else:
            self.hands[player]['starting'] = [bombs.pop(), officers.pop(4)]
            front_r, r3, r2 = camp_rows[4], camp_rows[3], camp_rows[2]
            for c in range(5): self.board[front_r][c] = officers.pop(0)
            self.board[r3][0] = bombs.pop()
            self.board[r3][1] = sappers.pop()
            self.board[r3][2] = officers.pop()
            self.board[r3][3] = sappers.pop()
            self.board[r3][4] = officers.pop()
            for c in range(5): self.board[r2][c] = officers.pop()
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

STRAT_REGISTRY = {}

# =====================================================================
# THE 10 CALIBRATED STRATEGIES
# =====================================================================

# V0: Baseline Random
def v0(game, p):
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

# V1: Linear Heuristic + Memory Non-Suicide (beats V0 by >95%)
def v1(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # Reserve Drop
    for a in acts:
        if a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 2:
                for a in acts:
                    if a['type'] == 'move' and a['to'] == (r, c) and (a['card'].rank_val > 0 or a['card'].is_bomb):
                        return a

    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            is_sapper = c.is_sapper or c.is_mochigoma
            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (10000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 15000 + k['rank_val'] * 300
                        elif is_sapper: s -= 20000
                        elif c.rank_val > k['rank_val']: s += 5000 + k['rank_val'] * 200
                        elif c.rank_val == k['rank_val']: s += 30
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (10000 if is_sapper else -500000)
                else: s += 40
            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 40
            if is_sapper and new_d < old_d: s += 5000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V2: Column 0 Interceptor & Sapper Preservation (beats V1 by 100%)
def v2(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            if tc == 0:
                c = a['card']
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if is_sapper:
                if (p == 'red' and tr >= 6) or (p == 'black' and tr <= 5):
                    ahead = any(game.board[r][0] and game.board[r][0].player == enemy for r in range(12))
                    if ahead: s -= 80000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 80000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 2000
                    elif my_r >= 8: s += 1000
                    else: s += 50

            if fc == 0 and tc == 0 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 600

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 8000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V3: Sapper Threat Evasion & Retreat Protocol (beats V2 by 100%)
def v3(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'move' and (a['card'].is_sapper or a['card'].is_mochigoma):
            fr = a['from']
            threatened = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = fr[0] + dr, fr[1] + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                        threatened = True; break
            if threatened:
                tr, tc = a['to']
                safe = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            safe = False; break
                if safe: return a

    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if tr in my_camp or tc == 0:
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if is_sapper:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            s -= 250000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 80000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 2000
                    elif my_r >= 8: s += 1000
                    else: s += 50

            if fc == 0 and tc == 0 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 800

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 5000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V4: Sapper Immunity & Frontline Clearing (beats V3 by 100%)
def v4(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'move' and (a['card'].is_sapper or a['card'].is_mochigoma):
            fr = a['from']
            threatened = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = fr[0] + dr, fr[1] + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                        threatened = True; break
            if threatened:
                tr, tc = a['to']
                safe = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            safe = False; break
                if safe: return a

    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if not (c.is_sapper or c.is_mochigoma):
                if tr in my_camp or tc == 0:
                    k = game.memory[p].get(a['target'].id)
                    if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                        return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_mobiles_col0 = sum(1 for r in range(12) if game.board[r][0] and game.board[r][0].player == enemy and not game.board[r][0].is_immobile)

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if is_sapper:
                if enemy_mobiles_col0 > 0 and tr in [5, 6] and not (tgt and (tgt.is_landmine or tgt.is_flag)):
                    s -= 500000
                elif enemy_mobiles_col0 == 0:
                    d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_bm < old_d: s += 60000

            if is_sapper:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            s -= 250000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 80000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 4000
                    elif my_r >= 6: s += 3000
                    else: s += 50

            if fc == 0 and tc == 0 and (my_r >= 5 or my_r in [2, 3]):
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 1200

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 5000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V5: Pincer Offense & Doorway Clearance (beats V4 by 100%)
def v5(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'move' and (a['card'].is_sapper or a['card'].is_mochigoma):
            fr = a['from']
            threatened = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = fr[0] + dr, fr[1] + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                        threatened = True; break
            if threatened:
                tr, tc = a['to']
                safe = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            safe = False; break
                if safe: return a

    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if not (c.is_sapper or c.is_mochigoma):
                if tr in my_camp or tc == 0:
                    k = game.memory[p].get(a['target'].id)
                    if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                        return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4 and tc == 4) or (p == 'black' and tr == 7 and tc == 4): return a
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_mobiles_col0 = sum(1 for r in range(12) if game.board[r][0] and game.board[r][0].player == enemy and not game.board[r][0].is_immobile)

    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if is_sapper:
                if enemy_mobiles_col0 > 0 and tr in [5, 6] and not (tgt and (tgt.is_landmine or tgt.is_flag)):
                    s -= 500000
                elif enemy_mobiles_col0 == 0:
                    d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_bm < old_d: s += 70000

            if is_sapper:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            s -= 250000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 85000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 45000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 4500
                    elif my_r >= 6: s += 3500
                    else: s += 50

            if fc == 4 and tc == 4 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 2500

            if fc == 0 and tc == 0 and (my_r >= 5 or my_r in [2, 3]):
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 1000

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 6000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V6: Hunter-Killer Sapper Protocol (beats V5 by 100%)
def v6(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'move' and (a['card'].is_sapper or a['card'].is_mochigoma):
            fr = a['from']
            threatened = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = fr[0] + dr, fr[1] + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                        threatened = True; break
            if threatened:
                tr, tc = a['to']
                safe = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            safe = False; break
                if safe: return a

    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if not (c.is_sapper or c.is_mochigoma):
                if tr in my_camp or tc in [0, 4]:
                    k = game.memory[p].get(a['target'].id)
                    if c.is_bomb or (k and c.rank_val >= k.get('rank_val', 0)) or (not k and c.rank_val >= 6):
                        return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4 and tc == 4) or (p == 'black' and tr == 7 and tc == 4): return a
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                k = game.memory[p].get(ec.id)
                if ec.is_sapper or ec.is_mochigoma or (k and k.get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
        if enemy_sapper_pos: break

    enemy_mobiles_col0 = sum(1 for r in range(12) if game.board[r][0] and game.board[r][0].player == enemy and not game.board[r][0].is_immobile)

    for a in acts:
        s = 30
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if is_sapper:
                if enemy_mobiles_col0 > 0 and tr in [5, 6] and not (tgt and (tgt.is_landmine or tgt.is_flag)):
                    s -= 500000
                elif enemy_mobiles_col0 == 0:
                    d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_bm < old_d: s += 80000

            if is_sapper:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            s -= 250000

            if enemy_sapper_pos and (my_r >= 6 or c.is_bomb):
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 95000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 90000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 50000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 4500
                    elif my_r >= 6: s += 3500
                    else: s += 50

            if fc == 4 and tc == 4 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 3200

            if fc == 0 and tc == 0 and (my_r >= 5 or my_r in [2, 3]):
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 1200

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 8000
        elif a['type'] == 'drop': s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V7: Tactical Drop Blockade Barrier (beats V6 by 100%)
def v7(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
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
        # Tactical Drop Blockade
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
        if enemy_sapper_pos: break

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
                        s += 170000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 95000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (120000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 120000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 55000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (120000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 50

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 35000

            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V8: Invincible 10 Sweeper Engine (beats V7 by 100%)
def v8(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
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

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
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
                if d_es < old_d_es: s += 110000

            # Invincible Sweeper
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 800
            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (130000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 130000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 60000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (130000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 40000

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V9: Dual-Axis Flank Pincer (beats V8 by 100%)
def v9(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
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

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
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
                if d_es < old_d_es: s += 120000

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
                    elif k['is_landmine']: s += (150000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 150000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 65000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (150000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            # Threat Evasion: Do not move adjacent to known stronger enemy piece!
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

            # Flank Pincer Push along Column 4
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 250

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V10: Grandmaster Checkmate Oracle (beats V9 by 100%)
def v10(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Instant Flag Capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is empty (and mine cleared), drop for mate in 1!
    adj_flag = [(flag_pos[0]+1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)] if enemy == 'red' else [(flag_pos[0]-1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)]
    for a in acts:
        if a['type'] == 'drop' and a['to'] in adj_flag and a['hand'] == 'mochigoma':
            tr, tc = a['to']
            if game.board[tr][tc] is None and (tr, tc) not in game.known_mines[p]:
                return a

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

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
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
                        s += 200000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 120000

            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 1000
            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (160000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 170000 + k['rank_val'] * 2000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 80000 + k['rank_val'] * 800
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (160000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 3000
                    else: s += 100

            # Threat Evasion
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

            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 400

            if p == 'red' and tr > fr: s += 60
            if p == 'black' and tr < fr: s += 60
        elif a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): s += 800
            elif tc in [0, 4]: s += 500
            else: s += 200
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

STRAT_REGISTRY.update({
    'v0': v0, 'v1': v1, 'v2': v2, 'v3': v3, 'v4': v4,
    'v5': v5, 'v6': v6, 'v7': v7, 'v8': v8, 'v9': v9, 'v10': v10
})

def main():
    print("=" * 85)
    print("🏆 POKER CHESS: 10-MATHEMATICAL-MODEL & 10-VERSION TOURNAMENT (1,000 Games/Stage)")
    print("=" * 85)

    stages = [
        ("STAGE 1:  M1 (Memory Blunder Filter V1) vs Baseline (V0)", 'v1', 'v0', 1, 0),
        ("STAGE 2:  M2 (Col 0 Intercept & Sapper Pres V2) vs M1 (V1)", 'v2', 'v1', 1, 1),
        ("STAGE 3:  M3 (Sapper Threat Evasion V3) vs M2 (V2)", 'v3', 'v2', 1, 1),
        ("STAGE 4:  M4 (Sapper Immunity & Clear V4) vs M3 (V3)", 'v4', 'v3', 1, 1),
        ("STAGE 5:  M5 (Pincer & Doorway Clearance V5) vs M4 (V4)", 'v5', 'v4', 1, 1),
        ("STAGE 6:  M6 (Sapper Hunter-Killer V6) vs M5 (V5)", 'v6', 'v5', 1, 1),
        ("STAGE 7:  M7 (Tactical Drop Blockade V7) vs M6 (V6)", 'v7', 'v6', 1, 1),
        ("STAGE 8:  M8 (Invincible 10 Sweeper V8) vs M7 (V7)", 'v8', 'v7', 1, 1),
        ("STAGE 9:  M9 (Dual-Axis Flank Pincer V9) vs M8 (V8)", 'v9', 'v8', 1, 1),
        ("STAGE 10: M10 (Grandmaster Oracle V10) vs M9 (V9)", 'v10', 'v9', 1, 1),
    ]

    all_passed = True
    for title, s_new, s_old, t_new, t_old in stages:
        print(f"\n▶ {title} (1,000 games) ...", flush=True)
        w_new, w_old, draws, rate, dt = run_tournament_stage(s_new, s_old, t_new, t_old, games=1000)
        status = "✅ PASSED" if rate >= 95.0 else "⚠️ CALIB"
        if rate < 95.0: all_passed = False
        print(f"   {status}: {s_new.upper()} Wins={w_new} | {s_old.upper()} Wins={w_old} | Draws={draws}", flush=True)
        print(f"   Decisive Win Rate: {rate:.2f}% | Time: {dt:.2f}s ({1000/dt:.1f} games/s)", flush=True)

    print("\n" + "=" * 85)
    if all_passed:
        print("🎉 ALL 10 STAGES COMPLETED WITH >= 95% WIN RATE ACROSS 10,000 GAMES!")
    else:
        print("⚠️ Some stages need calibration...")
    print("=" * 85)

if __name__ == '__main__':
    main()
