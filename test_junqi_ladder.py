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
    __slots__ = ('id', 'player', 'suit', 'rank', 'is_joker', 'is_flag', 'is_bomb', 'is_landmine', 'is_sapper', 'is_mochigoma', 'face_up', 'has_moved', 'move_count')
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
        self.move_count = 0

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
        self.turn_number = 0

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
            # Grandmaster Junqi Formation:
            # Frontline: Small probes (2, 2, 3, 3, 4)
            # Row 3: Bombs & Sappers in second echelon
            # Staging: Heavy officers (10, 9, 8) concealed deep
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
        if self.game_state != 'playing': return []
        moves = []
        for r in range(12):
            for c in range(5):
                card = self.board[r][c]
                if card and card.player == player and not card.is_immobile:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 12 and 0 <= nc < 5:
                            tgt = self.board[nr][nc]
                            if tgt is None or tgt.player != player:
                                moves.append({
                                    'type': 'move', 'card': card,
                                    'from': (r, c), 'to': (nr, nc), 'target': tgt
                                })

        drops = []
        for h_type in ['starting', 'mochigoma']:
            for i, c in enumerate(self.hands[player][h_type]):
                if h_type == 'starting':
                    valid_rows = [0, 1, 2, 3, 4] if player == 'red' else [11, 10, 9, 8, 7]
                else:
                    valid_rows = range(12)
                for r in valid_rows:
                    for col in range(5):
                        if self.board[r][col] is None:
                            drops.append({
                                'type': 'drop', 'card': c,
                                'hand': h_type, 'idx': i, 'to': (r, col)
                            })
        return moves + drops

    def execute(self, act):
        p = self.current_turn
        enemy = 'black' if p == 'red' else 'red'
        self.turn_number += 1

        if act['type'] == 'move':
            fr, fc = act['from']
            tr, tc = act['to']
            att = self.board[fr][fc]
            tgt = self.board[tr][tc]
            self.board[fr][fc] = None
            att.has_moved = True
            att.move_count += 1

            if tgt is None:
                self.board[tr][tc] = att
            else:
                self.resolve_clash(att, tgt, tr, tc)
        elif act['type'] == 'drop':
            h_type, idx = act['hand'], act['idx']
            tr, tc = act['to']
            c = self.hands[p][h_type].pop(idx)
            c.has_moved = True
            c.move_count = 1
            self.board[tr][tc] = c

        self.current_turn = enemy
        acts = self.get_actions(enemy)
        if not acts:
            self.game_state = 'ended'
            self.winner = p
            self.win_reason = 'Stalemate'

    def resolve_clash(self, att, tgt, r, c):
        p = att.player
        enemy = tgt.player

        for obs in ['red', 'black']:
            self.memory[obs][att.id] = {
                'rank': att.rank, 'rank_val': att.rank_val,
                'is_bomb': att.is_bomb, 'is_landmine': att.is_landmine,
                'is_flag': att.is_flag, 'is_sapper': att.is_sapper
            }
            self.memory[obs][tgt.id] = {
                'rank': tgt.rank, 'rank_val': tgt.rank_val,
                'is_bomb': tgt.is_bomb, 'is_landmine': tgt.is_landmine,
                'is_flag': tgt.is_flag, 'is_sapper': tgt.is_sapper
            }
            if tgt.is_landmine:
                self.known_mines[obs].add((r, c))

        if tgt.is_flag:
            self.winner = p
            self.win_reason = 'Captured Flag'
            self.game_state = 'ended'
            self.board[r][c] = att
            return

        if att.is_bomb or tgt.is_bomb:
            self.graveyard.extend([att, tgt])
            self.board[r][c] = None
            return

        if tgt.is_landmine:
            if att.is_sapper or att.is_mochigoma:
                self.capture(p, tgt)
                self.board[r][c] = att
                for obs in ['red', 'black']:
                    self.known_mines[obs].discard((r, c))
            else:
                self.graveyard.append(att)
                self.board[r][c] = tgt
            return

        if att.is_mochigoma and tgt.is_mochigoma:
            self.graveyard.extend([att, tgt])
            self.board[r][c] = None
            return

        if att.is_sapper and tgt.is_sapper and not att.is_mochigoma and not tgt.is_mochigoma:
            self.graveyard.extend([att, tgt])
            self.board[r][c] = None
            return

        if (att.is_sapper and not att.is_mochigoma) and tgt.is_mochigoma:
            self.graveyard.append(tgt)
            self.board[r][c] = att
            return

        if att.is_mochigoma and (tgt.is_sapper and not tgt.is_mochigoma):
            self.graveyard.append(att)
            self.board[r][c] = tgt
            return

        if att.is_mochigoma:
            self.graveyard.append(att)
            self.board[r][c] = tgt
            return

        if tgt.is_mochigoma:
            self.graveyard.append(tgt)
            self.board[r][c] = att
            return

        if att.is_sapper and not att.is_mochigoma:
            self.capture(enemy, att)
            self.board[r][c] = tgt
            return

        if tgt.is_sapper and not tgt.is_mochigoma:
            self.capture(p, tgt)
            self.board[r][c] = att
            return

        ar, dr = att.rank_val, tgt.rank_val
        if ar > dr:
            self.capture(p, tgt)
            self.board[r][c] = att
        elif ar < dr:
            self.capture(enemy, att)
            self.board[r][c] = tgt
        else:
            self.graveyard.extend([att, tgt])
            self.board[r][c] = None

    def capture(self, capturer, card):
        card.player = capturer
        card.is_mochigoma = True
        card.is_flag = False
        card.is_landmine = False
        card.is_bomb = False
        card.is_sapper = True
        self.hands[capturer]['mochigoma'].append(card)

print("Engine initialized successfully.")
