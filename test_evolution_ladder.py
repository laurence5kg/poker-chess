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

class FastGame:
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

        # Corner Flag Fortress
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
            # Optimal Mathematical Formation:
            # Column 0: Vanguard Infiltration Spearhead!
            # (4, 0) - Front: 10 (Field Marshal - clears all enemy mobile units)
            # (3, 0) - Second: Sapper (A - protected behind 10, ready to defuse barrier mine)
            # (2, 0) - Third: 9 (General - backup escort)
            # Reserve in hand: 1 Sapper, 1 Bomb (ready for drop)
            self.hands[player]['starting'] = [sappers.pop(), bombs.pop()]

            front_r, r3, r2, r1, r0 = camp_rows[4], camp_rows[3], camp_rows[2], camp_rows[1], camp_rows[0]
            ten_a, ten_b = officers.pop(), officers.pop() # 10, 10
            nine_a, nine_b = officers.pop(), officers.pop() # 9, 9
            eight_a, eight_b = officers.pop(), officers.pop() # 8, 8

            # Col 0: 10 in front, Sapper behind, 9 behind sapper
            self.board[front_r][0] = ten_a
            self.board[r3][0] = sappers.pop() # the other Sapper
            self.board[r2][0] = nine_a

            # Col 1: Bomb on r3 to ambush enemy counter-attacks
            self.board[r3][1] = bombs.pop()

            # Frontline cols 1, 2, 3, 4: Probes & anchors (2, 3, 4, 10)
            self.board[front_r][1] = officers.pop(0) # 2
            self.board[front_r][2] = officers.pop(0) # 2
            self.board[front_r][3] = officers.pop(0) # 3
            self.board[front_r][4] = ten_b # 10 anchors right flank

            # Row 3 remaining:
            self.board[r3][2] = eight_a
            self.board[r3][3] = eight_b
            self.board[r3][4] = nine_b

            # Fill remaining cells in r2, r1, r0
            rem = officers
            random.shuffle(rem)
            for r in [r2, r1, r0]:
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
        # Drops
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
# STRATEGIES
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
                s += 30
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

            if (tr, tc) == flag_pos:
                a['s'] = 500000; return a

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                if cid in game.memory[p]:
                    k = game.memory[p][cid]
                    if k['is_flag']: a['s'] = 500000; return a
                    elif k['is_landmine']:
                        s += 8000 if is_sapper else -30000
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

            # Advance toward enemy baseline
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
        if a['type'] == 'move' and a['to'] == flag_pos:
            return a
        if a['target'] and a['target'].player == enemy and a['target'].is_flag:
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
                    if k['is_flag']: a['s'] = 999999; return a
                    elif k['is_landmine']:
                        s += 25000 if is_sapper else -50000
                    elif k['rank_val'] > 0:
                        if c.is_bomb:
                            s += 35000 + k['rank_val'] * 500 # Bomb assassinates high officer!
                        elif is_sapper:
                            s -= 30000
                        elif my_r > k['rank_val']:
                            s += 8000 + k['rank_val'] * 300
                        else:
                            s -= 35000
                    elif k['is_mochigoma']:
                        s += 4000 if my_r > 0 else 50
                elif (tr, tc) in game.known_mines[p]:
                    s += 25000 if is_sapper else -50000
                else:
                    # Unrevealed target
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        # Inside enemy bunker: ONLY SAPPER ALLOWED!
                        if is_sapper: s += 30000
                        else: s -= 60000
                    else:
                        if my_r in [2, 3, 4] or is_sapper: s += 300
                        elif my_r >= 8: s += 100 # Cautious advance
                        elif c.is_bomb: s += 20

            # Spearhead Corridor (Column 0 & 1):
            if is_sapper:
                # Sapper marches directly to barrier mine
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 1500
            elif my_r >= 9:
                # Heavy officer leads along Col 0
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 600

            # Forward bias
            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30

        elif a['type'] == 'drop':
            s += 30
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

def play_one_game(strat1, strat2, form1='spearhead', form2='spearhead', max_turns=300):
    g = FastGame(strat1, strat2, red_form=form1, blk_form=form2)
    turns = 0
    fn_map = {
        'v0': v0_baseline,
        'v1': v1_memory,
        'v2': v2_spearhead,
    }
    while g.game_state == 'playing' and turns < max_turns:
        p = g.current_turn
        strat_name = g.strats[p]
        act = fn_map[strat_name](g, p)
        if not act: break
        g.execute(act)
        turns += 1
    if g.game_state == 'playing':
        g.winner = 'draw'
        g.win_reason = 'Max turns'
    return g.winner, turns

def run_match(s_new, s_old, f_new='spearhead', f_old='random', n_games=1000):
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

if __name__ == '__main__':
    run_match('v1', 'v0', f_new='spearhead', f_old='random', n_games=1000)

