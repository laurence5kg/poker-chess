# =====================================================================
# 10-Iteration Exhaustive 1,000-Game Test & Debug Verification Suite
# Poker Shogi & Junqi (扑克暗军将棋)
#
# Covers:
#   Iteration 1: PvE Human=Red vs Bot=Black (AI Level: Low)
#   Iteration 2: PvE Human=Red vs Bot=Black (AI Level: Medium)
#   Iteration 3: PvE Human=Red vs Bot=Black (AI Level: High)
#   Iteration 4: PvE Human=Black vs Bot=Red (AI Level: Low, Bot moves first)
#   Iteration 5: PvE Human=Black vs Bot=Red (AI Level: Medium, Bot moves first)
#   Iteration 6: PvE Human=Black vs Bot=Red (AI Level: High, Bot moves first)
#   Iteration 7: PvP 1v1 Hotseat (5x12 Board, Red vs Black)
#   Iteration 8: PvP 2v2 Alliance Battle (15x15 Cross Board, Opposite Seating)
#   Iteration 9: PvP 2v2 Alliance Battle (15x15 Cross Board, Adjacent Seating)
#   Iteration 10: PvP 1v1v1v1 Free-For-All (15x15 Cross Board, FFA 4 Generals)
# =====================================================================

import random
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SUITS = {
    'red': ['♥', '♦'],
    'black': ['♠', '♣']
}
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
OFFICER_RANKS = {'10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

class Card:
    def __init__(self, player, suit, rank, is_joker=False, team=None):
        self.player = player
        self.original_owner = player
        self.team = team or player
        self.suit = suit
        self.rank = rank
        self.is_joker = is_joker
        self.is_flag = is_joker
        self.is_bomb = (rank == 'K')
        self.is_landmine = (rank in ['Q', 'J'])
        self.is_sapper = (rank == 'A')
        self.is_mochigoma = False
        self.face_up = False

    @property
    def is_immobile(self):
        return (self.is_flag or self.is_landmine) and not self.is_mochigoma

class GameEngine2P:
    def __init__(self, human_side='red', ai_level='medium', mode='pve'):
        self.mode = mode
        self.human_side = human_side
        self.bot_side = 'black' if human_side == 'red' else 'red'
        self.ai_level = ai_level
        self.board = [[None for _ in range(5)] for _ in range(12)]
        self.current_turn = 'red'
        self.game_state = 'playing'
        self.hands = {
            'red': {'starting': [], 'mochigoma': []},
            'black': {'starting': [], 'mochigoma': []}
        }
        self.graveyard = []
        self.winner = None
        self.win_reason = ''
        self.position_counts = {}
        self.init_ai_memory()

    def init_ai_memory(self):
        self.ai_memory = {'red': {}, 'black': {}}
        self.ai_known_landmines = {'red': set(), 'black': set()}

    def purge_card_from_ai_memory(self, card):
        if not card:
            return
        cid = id(card)
        for p in ['red', 'black']:
            if cid in self.ai_memory[p]:
                del self.ai_memory[p][cid]

    def get_known_card(self, r, c, viewer):
        card = self.board[r][c]
        if not card:
            return None
        if card.player == viewer or card.face_up:
            return {
                'player': card.player,
                'rank': card.rank,
                'rank_val': OFFICER_RANKS.get(card.rank, 0),
                'is_bomb': card.is_bomb,
                'is_landmine': card.is_landmine,
                'is_flag': card.is_flag,
                'is_sapper': card.is_sapper,
                'is_mochigoma': card.is_mochigoma
            }
        if (r, c) in self.ai_known_landmines[viewer]:
            return {
                'player': card.player,
                'rank': card.rank,
                'rank_val': 0,
                'is_bomb': False,
                'is_landmine': True,
                'is_flag': False,
                'is_sapper': False,
                'is_mochigoma': False
            }
        cid = id(card)
        if cid in self.ai_memory[viewer]:
            return self.ai_memory[viewer][cid]
        return None

    def create_deck(self, player):
        deck = []
        for suit in SUITS[player]:
            for rank in RANKS:
                deck.append(Card(player, suit, rank, False))
        deck.append(Card(player, '🃏', 'JOKER', True))
        return deck

    def auto_setup(self, player):
        deck = self.create_deck(player)
        flag = next(c for c in deck if c.is_flag)
        mines = [c for c in deck if c.is_landmine]
        mobiles = [c for c in deck if not c.is_immobile]
        random.shuffle(mobiles)

        # 2 mobile cards in starting reserves (never Flag or Landmines)
        self.hands[player]['starting'] = [mobiles.pop(), mobiles.pop()]
        self.hands[player]['mochigoma'] = []

        # Corner Flag Fortress (Flag in corner, 4 Landmines adjacent around it)
        corner_col = random.choice([0, 4])
        if player == 'red':
            if corner_col == 0:
                flag_pos = (0, 0)
                mine_positions = [(0, 1), (1, 0), (1, 1), (0, 2)]
            else:
                flag_pos = (0, 4)
                mine_positions = [(0, 3), (1, 4), (1, 3), (0, 2)]
            camp_rows = [0, 1, 2, 3, 4]
        else:
            if corner_col == 0:
                flag_pos = (11, 0)
                mine_positions = [(11, 1), (10, 0), (10, 1), (11, 2)]
            else:
                flag_pos = (11, 4)
                mine_positions = [(11, 3), (10, 4), (10, 3), (11, 2)]
            camp_rows = [11, 10, 9, 8, 7]

        self.board[flag_pos[0]][flag_pos[1]] = flag
        for idx, (mr, mc) in enumerate(mine_positions):
            self.board[mr][mc] = mines[idx]

        occupied = {flag_pos} | set(mine_positions)
        for r in camp_rows:
            for c in range(5):
                if (r, c) not in occupied:
                    c_card = mobiles.pop()
                    assert not c_card.is_immobile, "Immobile card misplaced in open camp cell!"
                    self.board[r][c] = c_card

    def reset_and_setup(self):
        self.board = [[None for _ in range(5)] for _ in range(12)]
        self.current_turn = 'red'
        self.game_state = 'playing'
        self.hands = {
            'red': {'starting': [], 'mochigoma': []},
            'black': {'starting': [], 'mochigoma': []}
        }
        self.graveyard = []
        self.winner = None
        self.win_reason = ''
        self.position_counts = {}
        self.init_ai_memory()

        self.auto_setup('red')
        self.auto_setup('black')
        self.record_position()

    def get_counts(self, player):
        native = 0
        mochigoma = 0
        for r in range(12):
            for c in range(5):
                card = self.board[r][c]
                if card and card.player == player:
                    if card.is_mochigoma:
                        mochigoma += 1
                    else:
                        native += 1
        native += len(self.hands[player]['starting'])
        mochigoma += len(self.hands[player]['mochigoma'])
        return native, mochigoma

    def check_and_enforce_mutiny(self, player):
        native, mochigoma = self.get_counts(player)
        while mochigoma > native:
            if self.hands[player]['mochigoma']:
                discarded = self.hands[player]['mochigoma'].pop()
                self.purge_card_from_ai_memory(discarded)
                self.graveyard.append(discarded)
            else:
                removed = False
                for r in range(12):
                    for c in range(5):
                        card = self.board[r][c]
                        if card and card.player == player and card.is_mochigoma:
                            self.purge_card_from_ai_memory(card)
                            self.graveyard.append(card)
                            self.board[r][c] = None
                            removed = True
                            break
                    if removed:
                        break
                if not removed:
                    break
            native, mochigoma = self.get_counts(player)

    def handle_capture(self, capturing_player, card):
        self.purge_card_from_ai_memory(card)
        # INVARIANT 3: Conscripts CANNOT be re-conscripted. Traitors executed to Graveyard!
        if card.is_mochigoma:
            self.graveyard.append(card)
            return

        card.player = capturing_player
        card.is_bomb = False
        card.is_landmine = False
        card.is_flag = False
        card.is_sapper = False
        card.is_mochigoma = False
        native, mochigoma = self.get_counts(capturing_player)
        if (mochigoma + 1) <= native:
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
                target = self.board[nr][nc]
                if not target or target.player != player:
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
                actions.append({'type': 'drop', 'hand': 'starting', 'index': idx, 'to': d, 'is_capture': False})
        for idx, c in enumerate(self.hands[player]['mochigoma']):
            for d in self.get_legal_drops(player):
                actions.append({'type': 'drop', 'hand': 'mochigoma', 'index': idx, 'to': d, 'is_capture': False})
        return actions

    def execute_move(self, fr, fc, tr, tc):
        attacker = self.board[fr][fc]
        defender = self.board[tr][tc]
        assert not attacker.is_immobile, "Immobile card attempted to move!"
        self.board[fr][fc] = None

        if not defender:
            self.board[tr][tc] = attacker
            self.finish_turn()
            return

        attacker.face_up = True
        defender.face_up = True

        # Record clash in AI Memory for both players
        for p in ['red', 'black']:
            self.ai_memory[p][id(attacker)] = {
                'player': attacker.player,
                'rank': attacker.rank,
                'rank_val': OFFICER_RANKS.get(attacker.rank, 0),
                'is_bomb': attacker.is_bomb,
                'is_landmine': attacker.is_landmine,
                'is_flag': attacker.is_flag,
                'is_sapper': attacker.is_sapper,
                'is_mochigoma': attacker.is_mochigoma
            }
            self.ai_memory[p][id(defender)] = {
                'player': defender.player,
                'rank': defender.rank,
                'rank_val': OFFICER_RANKS.get(defender.rank, 0),
                'is_bomb': defender.is_bomb,
                'is_landmine': defender.is_landmine,
                'is_flag': defender.is_flag,
                'is_sapper': defender.is_sapper,
                'is_mochigoma': defender.is_mochigoma
            }
            if defender.is_landmine:
                self.ai_known_landmines[p].add((tr, tc))

        # 1. Flag Assault
        if defender.is_flag:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.purge_card_from_ai_memory(defender)
            self.winner = attacker.player
            self.win_reason = f"{attacker.player.upper()} ASSASSINATED FLAG"
            self.game_state = 'gameover'
            self.check_and_enforce_mutiny('red')
            self.check_and_enforce_mutiny('black')
            return

        # 2. Bomb (King)
        if attacker.is_bomb or defender.is_bomb:
            self.graveyard.extend([attacker, defender])
            self.purge_card_from_ai_memory(attacker)
            self.purge_card_from_ai_memory(defender)
            for p in ['red', 'black']:
                self.ai_known_landmines[p].discard((tr, tc))
            self.board[tr][tc] = None
            self.finish_turn()
            return

        # 3. Landmine
        if defender.is_landmine:
            if attacker.is_sapper or attacker.is_mochigoma:
                for p in ['red', 'black']:
                    self.ai_known_landmines[p].discard((tr, tc))
                self.board[tr][tc] = attacker
                self.handle_capture(attacker.player, defender)
            else:
                self.board[tr][tc] = defender
                self.graveyard.append(attacker)
                self.purge_card_from_ai_memory(attacker)
            self.finish_turn()
            return

        # 4. Conscript vs Conscript: Mutual destruction
        if attacker.is_mochigoma and defender.is_mochigoma:
            self.graveyard.extend([attacker, defender])
            self.purge_card_from_ai_memory(attacker)
            self.purge_card_from_ai_memory(defender)
            self.board[tr][tc] = None
            self.finish_turn()
            return

        # 5. Native Sapper vs Native Sapper: Mutual destruction
        if (attacker.is_sapper and not attacker.is_mochigoma) and (defender.is_sapper and not defender.is_mochigoma):
            self.graveyard.extend([attacker, defender])
            self.purge_card_from_ai_memory(attacker)
            self.purge_card_from_ai_memory(defender)
            self.board[tr][tc] = None
            self.finish_turn()
            return

        # 6. Native Sapper vs Conscript: Native Sapper wins! Conscript executed to Graveyard
        if (attacker.is_sapper and not attacker.is_mochigoma) and defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.purge_card_from_ai_memory(defender)
            self.finish_turn()
            return
        if attacker.is_mochigoma and (defender.is_sapper and not defender.is_mochigoma):
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.purge_card_from_ai_memory(attacker)
            self.finish_turn()
            return

        # 7. Conscript vs Numbered Officer: Officer wins, Conscript executed to Graveyard
        if attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.purge_card_from_ai_memory(attacker)
            self.finish_turn()
            return
        if defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.purge_card_from_ai_memory(defender)
            self.finish_turn()
            return

        # 8. Native Sapper vs Numbered Officer: Officer wins, Native Sapper captured
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

        # 9. Officer vs Officer
        ar = OFFICER_RANKS[attacker.rank]
        dr = OFFICER_RANKS[defender.rank]
        if ar > dr:
            self.board[tr][tc] = attacker
            self.handle_capture(attacker.player, defender)
        elif ar < dr:
            self.board[tr][tc] = defender
            self.handle_capture(defender.player, attacker)
        else:
            self.graveyard.extend([attacker, defender])
            self.purge_card_from_ai_memory(attacker)
            self.purge_card_from_ai_memory(defender)
            self.board[tr][tc] = None
        self.finish_turn()

    def execute_drop(self, hand_type, index, tr, tc):
        card = self.hands[self.current_turn][hand_type].pop(index)
        if hand_type == 'starting':
            front_r = 4 if self.current_turn == 'red' else 7
            if card.is_immobile:
                assert tr != front_r, f"Illegal drop of immobile card on frontline {tr}!"
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

    def record_position(self):
        h = f"{self.current_turn}:" + ",".join(
            (c.player[0] + c.rank + ('M' if c.is_mochigoma else '')) if c else '0'
            for row in self.board for c in row
        )
        self.position_counts[h] = self.position_counts.get(h, 0) + 1
        return self.position_counts[h] >= 3

    def finish_turn(self):
        self.check_and_enforce_mutiny('red')
        self.check_and_enforce_mutiny('black')

        if self.record_position():
            self.winner = 'draw'
            self.win_reason = "THREEFOLD REPETITION"
            self.game_state = 'gameover'
            return

        next_turn = 'black' if self.current_turn == 'red' else 'red'
        self.current_turn = next_turn

        if not self.get_all_actions(self.current_turn):
            self.winner = 'black' if self.current_turn == 'red' else 'red'
            self.win_reason = f"{self.current_turn.upper()} STALEMATED"
            self.game_state = 'gameover'

    def verify_invariants(self):
        # 1. Total cards conservation = 54
        board_cards = [c for r in self.board for c in r if c]
        red_hands = self.hands['red']['starting'] + self.hands['red']['mochigoma']
        black_hands = self.hands['black']['starting'] + self.hands['black']['mochigoma']
        total = len(board_cards) + len(red_hands) + len(black_hands) + len(self.graveyard)
        assert total == 54, f"Card conservation violation: total={total} != 54"

        # 2. Mutiny invariant: mochigoma <= native
        for p in ['red', 'black']:
            n, m = self.get_counts(p)
            assert m <= n, f"Anti-mutiny invariant violated for {p}: mochigoma={m} > native={n}"

        # 3. No flag or mine on frontline
        for c in range(5):
            r_card = self.board[4][c]
            if r_card and r_card.player == 'red':
                assert not r_card.is_immobile, f"Red frontline violation at (4,{c})"
            b_card = self.board[7][c]
            if b_card and b_card.player == 'black':
                assert not b_card.is_immobile, f"Black frontline violation at (7,{c})"

    def choose_action(self, player, level):
        actions = self.get_all_actions(player)
        if not actions:
            return None

        if level == 'low':
            # 75% random, 25% capture
            captures = [a for a in actions if a['is_capture']]
            if captures and random.random() < 0.25:
                return random.choice(captures)
            return random.choice(actions)

        elif level == 'medium':
            # Heuristic scoring
            for a in actions:
                score = 10
                if a['type'] == 'move':
                    fr, fc = a['from']
                    tr, tc = a['to']
                    card = a['card']
                    target = a['target']
                    if player == 'black' and tr < fr: score += 15
                    if player == 'red' and tr > fr: score += 15
                    if target and target.player != player:
                        if target.is_flag: score += 10000
                        elif target.face_up and target.is_landmine:
                            score += (120 if (card.is_sapper or card.is_mochigoma) else -500)
                        elif card.is_bomb: score += 65
                        elif card.is_sapper or card.is_mochigoma: score += 35
                        elif target.face_up:
                            my_r = OFFICER_RANKS.get(card.rank, 0)
                            en_r = OFFICER_RANKS.get(target.rank, 0)
                            if my_r > en_r: score += 70
                            elif my_r == en_r: score += 30
                            else: score -= 300
                        else:
                            score += 30
                elif a['type'] == 'drop':
                    score += 20
                a['score'] = score
            actions.sort(key=lambda x: x['score'], reverse=True)
            top_slice = actions[:min(3, len(actions))]
            return random.choice(top_slice)

        else: # High (Memory-enabled Tactical & Sapper Hunting)
            enemy = 'black' if player == 'red' else 'red'
            enemy_flag_pos = None
            my_flag_pos = None
            for r in range(12):
                for c in range(5):
                    card = self.board[r][c]
                    if card:
                        if card.is_flag and card.player == enemy: enemy_flag_pos = (r, c)
                        if card.is_flag and card.player == player: my_flag_pos = (r, c)

            for a in actions:
                score = 15
                if a['type'] == 'move':
                    fr, fc = a['from']
                    tr, tc = a['to']
                    card = a['card']
                    target = a['target']
                    my_rank_val = OFFICER_RANKS.get(card.rank, 0)
                    is_my_sapper = card.is_sapper or card.is_mochigoma

                    # 1. Tactical Evaluation using AI Memory
                    if target and target.player == enemy:
                        known = self.get_known_card(tr, tc, player)
                        if known:
                            # A. Known Flag: Instant Win!
                            if known['is_flag']:
                                a['score'] = 50000
                                continue

                            # B. Known Landmine:
                            elif known['is_landmine']:
                                if is_my_sapper:
                                    score += 6000 # AI remembers landmine and sends sapper to clear it!
                                else:
                                    score -= 25000 # Non-sapper will NEVER attack known landmine!

                            # C. Known Officer:
                            elif known['rank_val'] > 0:
                                if card.is_bomb:
                                    score += 2500 + (known['rank_val'] * 200) # Bomb assassinates high officer
                                elif is_my_sapper:
                                    score -= 15000 # Sapper never attacks known officer!
                                else:
                                    if my_rank_val > known['rank_val']:
                                        score += 3000 + (known['rank_val'] * 200) # Bigger officer captures smaller!
                                    elif my_rank_val == known['rank_val']:
                                        score += 80 # Tied rank trade
                                    else:
                                        # Smaller card vs Bigger card: STRICTLY AVOIDED!
                                        score -= 20000

                            # D. Known Conscript Sapper:
                            elif known['is_mochigoma']:
                                if card.is_sapper and not card.is_mochigoma:
                                    score += 1800 # Native Sapper executes Conscript
                                elif my_rank_val > 0:
                                    score += 1500 # Officer executes Conscript
                                elif card.is_mochigoma:
                                    score += 40 # Conscript vs Conscript trade

                            # E. Known Bomb:
                            elif known['is_bomb']:
                                if my_rank_val >= 7:
                                    score -= 10000 # High officers avoid bomb
                                else:
                                    score -= 200
                        else:
                            # Unknown face-down enemy piece:
                            if card.is_bomb: score += 60
                            elif is_my_sapper: score += 45
                            elif my_rank_val >= 8: score += 70
                            else: score += 30

                    # 2. Sapper Pathing towards Known Enemy Landmines:
                    if is_my_sapper and len(self.ai_known_landmines[player]) > 0:
                        best_dist_diff = -999
                        for mr, mc in self.ai_known_landmines[player]:
                            old_d = abs(fr - mr) + abs(fc - mc)
                            new_d = abs(tr - mr) + abs(tc - mc)
                            diff = old_d - new_d
                            if diff > best_dist_diff:
                                best_dist_diff = diff
                        if best_dist_diff > 0:
                            score += 150 * best_dist_diff # Sapper actively hunts and moves towards landmines

                    # 3. Distance towards enemy baseline / Flag
                    if enemy_flag_pos:
                        old_d = abs(fr - enemy_flag_pos[0]) + abs(fc - enemy_flag_pos[1])
                        new_d = abs(tr - enemy_flag_pos[0]) + abs(tc - enemy_flag_pos[1])
                        if new_d < old_d: score += 20
                    else:
                        if player == 'black' and tr < fr: score += 15
                        if player == 'red' and tr > fr: score += 15

                    # 4. Defense: If our flag is under threat, protect it
                    if my_flag_pos:
                        to_flag_dist = abs(tr - my_flag_pos[0]) + abs(tc - my_flag_pos[1])
                        if to_flag_dist <= 2: score += 30

                    # 5. 2-Ply Threat Check using Memory:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = tr + dr, tc + dc
                        if 0 <= nr < 12 and 0 <= nc < 5:
                            ep = self.board[nr][nc]
                            if ep and ep.player == enemy:
                                k_enemy = self.get_known_card(nr, nc, player)
                                if k_enemy:
                                    if k_enemy['rank_val'] > my_rank_val:
                                        score -= 800 # Step away from known stronger officer
                                    elif k_enemy['is_bomb'] and my_rank_val >= 7:
                                        score -= 500
                                elif not ep.is_immobile:
                                    score -= 25
                elif a['type'] == 'drop':
                    score += 25
                a['score'] = score
            actions.sort(key=lambda x: x['score'], reverse=True)
            return actions[0]

    def play_game(self, max_turns=400):
        self.reset_and_setup()
        turn_count = 0

        while self.game_state == 'playing' and turn_count < max_turns:
            self.verify_invariants()
            p = self.current_turn

            if self.mode == 'pve':
                lvl = self.ai_level if p == self.bot_side else 'medium'
            else:
                lvl = 'medium'

            action = self.choose_action(p, lvl)
            if not action:
                self.winner = 'black' if p == 'red' else 'red'
                self.win_reason = f"{p.upper()} NO LEGAL MOVES"
                self.game_state = 'gameover'
                break

            if action['type'] == 'move':
                self.execute_move(action['from'][0], action['from'][1], action['to'][0], action['to'][1])
            else:
                self.execute_drop(action['hand'], action['index'], action['to'][0], action['to'][1])

            turn_count += 1

        if self.game_state == 'playing':
            self.winner = 'draw'
            self.win_reason = 'MAX TURNS EXCEEDED'
            self.game_state = 'gameover'

        self.check_and_enforce_mutiny('red')
        self.check_and_enforce_mutiny('black')
        self.verify_invariants()
        return self.winner, self.win_reason, turn_count


# =====================================================================
# 4-Player Simulation Engine for 2v2 and FFA
# =====================================================================
from test_simulation_4p import GameEngine4PSim, run_sim_game

def run_10_iteration_suite():
    print("=" * 70)
    print("🚀 EXECUTING 10-ITERATION COMPREHENSIVE TEST & DEBUG SUITE")
    print("   Total Tests: 1,000 Full Games Across All Modes, Sides, and AI Levels")
    print("=" * 70)

    start_time = time.time()
    total_games_played = 0
    total_violations = 0

    iterations = [
        ("Iteration 1: PvE (Human: RED vs Bot: BLACK) [AI: Low]", 'pve', 'red', 'low', 100),
        ("Iteration 2: PvE (Human: RED vs Bot: BLACK) [AI: Medium]", 'pve', 'red', 'medium', 100),
        ("Iteration 3: PvE (Human: RED vs Bot: BLACK) [AI: High]", 'pve', 'red', 'high', 100),
        ("Iteration 4: PvE (Human: BLACK vs Bot: RED) [AI: Low] - Bot Moves First", 'pve', 'black', 'low', 100),
        ("Iteration 5: PvE (Human: BLACK vs Bot: RED) [AI: Medium] - Bot Moves First", 'pve', 'black', 'medium', 100),
        ("Iteration 6: PvE (Human: BLACK vs Bot: RED) [AI: High] - Bot Moves First", 'pve', 'black', 'high', 100),
        ("Iteration 7: PvP 1v1 Classic Duel (5x12 Board, Red vs Black)", 'pvp', 'red', 'medium', 100),
        ("Iteration 8: PvP 2v2 Alliance Battle (15x15 Cross, Clubs vs Hearts, Opposite)", '2v2', 'opposite', 'medium', 100),
        ("Iteration 9: PvP 2v2 Alliance Battle (15x15 Cross, Clubs vs Hearts, Adjacent)", '2v2', 'adj_nw_se', 'medium', 100),
        ("Iteration 10: PvP 1v1v1v1 Free-For-All (15x15 Cross Board, FFA 4 Generals)", 'ffa', 'all', 'medium', 100),
    ]

    for idx, (title, mode, side_or_seat, ai_lvl, count) in enumerate(iterations, 1):
        print(f"\n▶ [{idx}/10] {title} ...")
        t0 = time.time()
        red_wins = 0
        black_wins = 0
        draws = 0
        moves_total = 0

        for g in range(count):
            try:
                if mode in ['pve', 'pvp']:
                    engine = GameEngine2P(human_side=side_or_seat, ai_level=ai_lvl, mode=mode)
                    winner, reason, turns = engine.play_game()
                    moves_total += turns
                    if winner == 'red': red_wins += 1
                    elif winner == 'black': black_wins += 1
                    else: draws += 1
                elif mode == '2v2':
                    if side_or_seat == 'opposite':
                        seat = {'a': 'red', 'c': 'red', 'b': 'black', 'd': 'black'}
                    elif side_or_seat == 'adj_nw_se':
                        seat = {'a': 'red', 'b': 'red', 'c': 'black', 'd': 'black'}
                    else:
                        seat = {'a': 'red', 'd': 'red', 'b': 'black', 'c': 'black'}
                    sim4p = GameEngine4PSim(mode='2v2', seating=seat)
                    for p in ['a', 'b', 'c', 'd']:
                        sim4p.auto_setup(p)
                    run_sim_game(sim4p, max_turns=200)
                    sim4p.check_invariants()
                    moves_total += sim4p.stats['moves']
                    if sim4p.winner == 'red': red_wins += 1
                    elif sim4p.winner == 'black': black_wins += 1
                    else: draws += 1
                elif mode == 'ffa':
                    sim4p = GameEngine4PSim(mode='ffa')
                    for p in ['a', 'b', 'c', 'd']:
                        sim4p.auto_setup(p)
                    run_sim_game(sim4p, max_turns=200)
                    sim4p.check_invariants()
                    moves_total += sim4p.stats['moves']
                    if sim4p.winner: red_wins += 1
                    else: draws += 1
                total_games_played += 1
            except AssertionError as e:
                total_violations += 1
                print(f"   ❌ INVARIANT FAILURE on game {g+1}: {e}")
                sys.exit(1)
            except Exception as e:
                total_violations += 1
                print(f"   ❌ CRASH on game {g+1}: {e}")
                sys.exit(1)

        dt = time.time() - t0
        print(f"   ✅ {count}/{count} Games Completed in {dt:.2f}s | "
              f"W/L/D: Red/A/C={red_wins}, Black/B/D={black_wins}, Draws={draws} | "
              f"Avg Turns: {moves_total/count:.1f} | 0 Invariant Violations")

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("🎯 FINAL 10-ITERATION STRESS TEST REPORT")
    print("=" * 70)
    print(f"Total Games Played:        {total_games_played:,}")
    print(f"Total Violations / Crashes: {total_violations}")
    print(f"Total Execution Time:      {total_time:.2f}s ({total_games_played/total_time:.1f} games/sec)")
    print(f"Pass Rate:                 100.0% (Zero Invariant Violations)")
    print("=" * 70)
    print("🏆 ALL 10 ITERATIONS PASSED PERFECTLY!\n")

if __name__ == '__main__':
    run_10_iteration_suite()
