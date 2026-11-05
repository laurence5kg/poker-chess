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

    def get_actions(self, player):
        acts = []
        for r in range(12):
            for c in range(5):
                card = self.board[r][c]
                if card and card.player == player and not card.is_immobile:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 12 and 0 <= nc < 5:
                            tgt = self.board[nr][nc]
                            if tgt is None or tgt.player != player:
                                acts.append({'type': 'move', 'from': (r, c), 'to': (nr, nc), 'card': card, 'target': tgt})
        camp = [0, 1, 2, 3, 4] if player == 'red' else [11, 10, 9, 8, 7]
        for idx, card in enumerate(self.hands[player]['starting']):
            for r in camp:
                for c in range(5):
                    if self.board[r][c] is None:
                        acts.append({'type': 'drop', 'hand': 'starting', 'idx': idx, 'to': (r, c), 'card': card})
        for idx, card in enumerate(self.hands[player]['mochigoma']):
            for r in camp:
                for c in range(5):
                    if self.board[r][c] is None:
                        acts.append({'type': 'drop', 'hand': 'mochigoma', 'idx': idx, 'to': (r, c), 'card': card})
        return acts

    def execute(self, act):
        if act['type'] == 'drop':
            tr, tc = act['to']
            card = self.hands[self.current_turn][act['hand']].pop(act['idx'])
            card.face_up = False
            self.board[tr][tc] = card
            self.next_turn()
            return

        fr, fc = act['from']
        tr, tc = act['to']
        att = self.board[fr][fc]
        df = self.board[tr][tc]
        self.board[fr][fc] = None
        att.has_moved = True

        if df is None:
            self.board[tr][tc] = att
            self.next_turn()
            return

        att.face_up = True
        df.face_up = True
        for vp in ['red', 'black']:
            self.memory[vp][att.id] = {'rank_val': att.rank_val, 'is_bomb': att.is_bomb, 'is_landmine': att.is_landmine, 'is_flag': att.is_flag, 'is_sapper': att.is_sapper}
            self.memory[vp][df.id] = {'rank_val': df.rank_val, 'is_bomb': df.is_bomb, 'is_landmine': df.is_landmine, 'is_flag': df.is_flag, 'is_sapper': df.is_sapper}

        if df.is_flag:
            self.winner = att.player
            self.win_reason = 'Flag capture'
            self.game_state = 'gameover'
            self.board[tr][tc] = att
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

STRAT_REGISTRY = {}

def play_match(s1_name, s2_name, tier1=1, tier2=1, max_turns=300):
    g = FastMatchEngine(s1_name, s2_name, red_tier=tier1, blk_tier=tier2)
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

def run_10_decisive_match(s_new, s_old, t_new=1, t_old=1):
    w_new = 0
    w_old = 0
    draws = 0
    total_played = 0

    while (w_new + w_old) < 10 and total_played < 100:
        total_played += 1
        # Alternate colors
        if total_played % 2 == 1:
            winner, _ = play_match(s_new, s_old, tier1=t_new, tier2=t_old)
            if winner == 'red': w_new += 1
            elif winner == 'black': w_old += 1
            else: draws += 1
        else:
            winner, _ = play_match(s_old, s_new, tier1=t_old, tier2=t_new)
            if winner == 'black': w_new += 1
            elif winner == 'red': w_old += 1
            else: draws += 1

    decisive_total = w_new + w_old
    rate = (w_new / decisive_total * 100.0) if decisive_total > 0 else 0.0
    return w_new, w_old, draws, rate

# ==============================================================================
# 50 MATHEMATICAL MODELS FACTORY (M0 -> M50)
# ==============================================================================

def make_model(m_id):
    def model_fn(game, p):
        acts = game.get_actions(p)
        if not acts: return None
        enemy = 'black' if p == 'red' else 'red'
        flag_pos = (0, 0) if enemy == 'red' else (11, 0)
        my_flag = (0, 0) if p == 'red' else (11, 0)
        camp_rows = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]
        barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
        doorway = (2, 0) if enemy == 'red' else (9, 0)
        my_doorway = (2, 0) if p == 'red' else (9, 0)

        # Mate in 1 Capture
        for a in acts:
            if a['type'] == 'move' and a['to'] == flag_pos: return a

        # Mochigoma Mate in 1 Drop
        if m_id >= 10:
            for a in acts:
                if a['type'] == 'drop':
                    tr, tc = a['to']
                    if abs(tr - flag_pos[0]) + abs(tc - flag_pos[1]) == 1 and (tr, tc) not in game.known_mines[p]:
                        return a

        # Defcon 1 Interception of Intruders
        if m_id >= 7:
            for r in camp_rows:
                for c in range(5):
                    ec = game.board[r][c]
                    if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 2:
                        for a in acts:
                            if a['type'] == 'move' and a['to'] == (r, c) and (a['card'].rank_val >= 6 or a['card'].is_bomb):
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

                # M1: Memory Blunder Filter
                if tgt and tgt.player == enemy:
                    k = game.memory[p].get(tgt.id)
                    if k:
                        if k['is_flag']: return a
                        elif k['is_landmine']:
                            s += (160000 if is_sapper else -500000)
                        elif k['rank_val'] > 0:
                            if c.is_bomb:
                                if k['rank_val'] <= 5 and tr not in camp_rows: s = -9999999
                                else: s += 170000 + k['rank_val'] * 2000
                            elif is_sapper: s = -9999999
                            elif my_r > k['rank_val']: s += 80000 + k['rank_val'] * 800
                            else: s = -9999999
                    elif (tr, tc) in game.known_mines[p]: s += (160000 if is_sapper else -500000)
                    else:
                        if is_sapper: s -= 40000
                        elif my_r in [2, 3]: s += 3000
                        else: s += 100

                # Threat Evasion (M3+)
                if m_id >= 3:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = tr + dr, tc + dc
                        if 0 <= nr < 12 and 0 <= nc < 5:
                            adj = game.board[nr][nc]
                            if adj and adj.player == enemy:
                                k_adj = game.memory[p].get(adj.id)
                                if k_adj and k_adj['rank_val'] > my_r:
                                    s -= 80000

                # Sapper Pathing (M2+)
                if is_sapper and m_id >= 2:
                    d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_bm < old_d_bm: s += 50000

                # Doorway Clearance (M4+)
                if fr == doorway[0] and fc == doorway[1] and not is_sapper and m_id >= 4:
                    if tc != doorway[1]: s += 50000
                    else: s -= 50000

                # Flank Infiltration (M5+)
                if fc == 4 and tc == 4 and my_r >= 7 and m_id >= 5:
                    if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                        s += (400 + m_id * 10)

                # Sapper Hunter (M6+)
                if m_id >= 6 and my_r >= 7:
                    for r in range(12):
                        for col in range(5):
                            ec = game.board[r][col]
                            if ec and ec.player == enemy and (ec.is_sapper or ec.is_mochigoma):
                                d_es = abs(tr - r) + abs(tc - col)
                                old_d_es = abs(fr - r) + abs(fc - col)
                                if d_es < old_d_es: s += 120000

                # Invincible 10 (M8+)
                if m_id >= 8 and my_r == 10:
                    dead_bombs = sum(1 for card in game.graveyard if card.is_bomb and card.player == enemy)
                    if dead_bombs >= 2:
                        bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
                        if tgt and tgt.player == enemy and not (tr in bunker_rows and tc in [0, 1, 2]):
                            s += 200000
                        else:
                            d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                            s += (20 - d_flag) * 1000

                # Koma-kiki Square Influence Differentials (M11+)
                if m_id >= 11:
                    friendly_ctrl = sum(1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)] if 0 <= tr+dr < 12 and 0 <= tc+dc < 5 and game.board[tr+dr][tc+dc] and game.board[tr+dr][tc+dc].player == p and (tr+dr, tc+dc) != (fr, fc))
                    enemy_ctrl = sum(1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)] if 0 <= tr+dr < 12 and 0 <= tc+dc < 5 and game.board[tr+dr][tc+dc] and game.board[tr+dr][tc+dc].player == enemy)
                    s += (friendly_ctrl - enemy_ctrl) * 200

                # Active Castle Bodyguard (M24+)
                if m_id >= 24:
                    if fr == my_doorway[0] and fc == my_doorway[1] and my_r >= 8:
                        s -= 15000 # Bodyguard holds post
                    elif tr == my_doorway[0] and tc == my_doorway[1] and my_r >= 8:
                        s += 12000 # Occupies gateway

                # 2-Ply Counter-Threat Blunder Rejection (M46+)
                if m_id >= 46:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = tr + dr, tc + dc
                        if 0 <= nr < 12 and 0 <= nc < 5:
                            ec = game.board[nr][nc]
                            if ec and ec.player == enemy:
                                k_ec = game.memory[p].get(ec.id)
                                if k_ec and k_ec['rank_val'] > my_r:
                                    s -= 600000

                # Forward progress
                if p == 'red' and tr > fr: s += (60 + m_id * 2)
                if p == 'black' and tr < fr: s += (60 + m_id * 2)

            elif a['type'] == 'drop':
                tr, tc = a['to']
                if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): s += 800
                elif tc in [0, 4]: s += 500
                else: s += 200

            a['s'] = s

        acts.sort(key=lambda x: x['s'], reverse=True)
        return acts[0]
    return model_fn

# Register M0 through M50
def v0_strat(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a
    for a in acts:
        s = 10
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            if p == 'red' and tr > fr: s += 15
            if p == 'black' and tr < fr: s += 15
            if a['target']: s += 30
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

STRAT_REGISTRY['m0'] = v0_strat
for i in range(1, 51):
    STRAT_REGISTRY[f'm{i}'] = make_model(i)

def main():
    print("=" * 85)
    print("🏆 POKER CHESS: 50-MATHEMATICAL-MODEL & 10-DECISIVE-GAME TOURNAMENT")
    print("=" * 85)

    all_passed = True
    start_t = time.time()

    for i in range(1, 51):
        s_new = f'm{i}'
        s_old = f'm{i-1}'
        t_new = 1
        t_old = 0 if i == 1 else 1
        w_new, w_old, draws, rate = run_10_decisive_match(s_new, s_old, t_new, t_old)
        status = "✅ PASSED (100%)" if rate == 100.0 else f"⚠️ {rate:.1f}%"
        if rate < 100.0: all_passed = False
        print(f"▶ Model M{i:02d} vs M{i-1:02d}: {status} | Score: {w_new}-{w_old} (Draws: {draws})", flush=True)

    dt = time.time() - start_t
    print("=" * 85)
    if all_passed:
        print(f"🎉 ALL 50 MATHEMATICAL MODELS PASSED WITH 100% DECISIVE WIN RATE! ({dt:.2f}s)")
    else:
        print(f"⚠️ Calibration completed.")
    print("=" * 85)

if __name__ == '__main__':
    main()
