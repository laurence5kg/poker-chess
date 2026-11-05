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
            self.hands[player]['starting'] = [bombs.pop(), officers.pop(4)] # Bomb + rank 6
            front_r, r3, r2 = camp_rows[4], camp_rows[3], camp_rows[2]
            for c in range(5): self.board[front_r][c] = officers.pop(0) # ranks 2, 2, 3, 3, 4
            self.board[r3][0] = bombs.pop()
            self.board[r3][1] = sappers.pop()
            self.board[r3][2] = officers.pop() # rank 10
            self.board[r3][3] = sappers.pop()
            self.board[r3][4] = officers.pop() # rank 9
            for c in range(5): self.board[r2][c] = officers.pop() # ranks 8, 8, 7, 7, 6
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
