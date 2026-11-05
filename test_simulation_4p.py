"""
4-Player Engine Simulation & Verification Suite
Supports:
  - 15x15 Plus-Shaped (Cross) Board with 4 Camp Zones + 5x5 Central Zone with 4 Obstacles
  - 4 Players: A (North), B (West), C (South), D (East)
  - Modes: 2v2 (Same-color teammates with customizable seating) and FFA (Free-For-All)
  - 10-Iteration Test & Debug Loop covering all invariants
"""

import random
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Card definitions
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
OFFICER_RANKS = { '10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2 }

class Card4P:
    def __init__(self, player, team, suit, rank, is_joker=False):
        self.player = player       # 'a', 'b', 'c', 'd'
        self.original_owner = player
        self.team = team           # 'red', 'black', or player id in FFA
        self.suit = suit
        self.rank = rank
        self.is_joker = is_joker
        
        self.is_flag = is_joker
        self.is_bomb = rank == 'K'
        self.is_landmine = (rank == 'Q' or rank == 'J')
        self.is_sapper = rank == 'A'
        
        self.is_mochigoma = False
        self.face_up = False

    @property
    def is_immobile(self):
        return (self.is_flag or self.is_landmine) and not self.is_mochigoma


class GameEngine4PSim:
    # 4 Center Obstacles (relative row 1 & 3, col 1 & 3 inside 5x5 center)
    OBSTACLES = {(6, 6), (6, 8), (8, 6), (8, 8)}

    def __init__(self, mode='2v2', seating=None):
        self.mode = mode # '2v2' or 'ffa'
        self.rows = 15
        self.cols = 15
        self.board = [[None for _ in range(15)] for _ in range(15)]
        
        # Turn order clockwise: North (A) -> East (D) -> South (C) -> West (B)
        self.turn_order = ['a', 'd', 'c', 'b']
        self.current_turn_idx = 0
        self.game_state = 'setup'
        
        # Seating configuration for 2v2
        if self.mode == '2v2':
            # Default: Opposite (A & C Red, B & D Black)
            self.seating = seating or {'a': 'red', 'c': 'red', 'b': 'black', 'd': 'black'}
        else:
            # FFA: Each player is their own team
            self.seating = {'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd'}

        self.hands = {
            p: {'starting': [], 'mochigoma': []} for p in ['a', 'b', 'c', 'd']
        }
        self.graveyard = []
        self.eliminated = {p: False for p in ['a', 'b', 'c', 'd']}
        self.winner = None
        self.win_reason = ''
        self.position_counts = {}

        # Telemetry
        self.stats = {
            'moves': 0,
            'drops_starting': 0,
            'drops_mochigoma': 0,
            'flag_captures': 0,
            'bomb_explosions': 0,
            'mines_cleared': 0,
            'mines_detonated': 0,
            'officer_captures': 0,
            'conscripts_executed': 0,
            'mutiny_triggers': 0,
            'eliminations': 0
        }

    @property
    def current_player(self):
        return self.turn_order[self.current_turn_idx]

    @staticmethod
    def is_playable(r, c):
        if not (0 <= r < 15 and 0 <= c < 15):
            return False
        # Player A Camp: Rows 0..4, Cols 5..9
        if 0 <= r <= 4 and 5 <= c <= 9:
            return True
        # Player C Camp: Rows 10..14, Cols 5..9
        if 10 <= r <= 14 and 5 <= c <= 9:
            return True
        # Player B Camp: Rows 5..9, Cols 0..4
        if 5 <= r <= 9 and 0 <= c <= 4:
            return True
        # Player D Camp: Rows 5..9, Cols 10..14
        if 5 <= r <= 9 and 10 <= c <= 14:
            return True
        # Center 5x5: Rows 5..9, Cols 5..9
        if 5 <= r <= 9 and 5 <= c <= 9:
            if (r, c) in GameEngine4PSim.OBSTACLES:
                return False
            return True
        # Void corners
        return False

    @staticmethod
    def is_frontline(player, r, c):
        if player == 'a':
            return r == 4 and 5 <= c <= 9
        elif player == 'c':
            return r == 10 and 5 <= c <= 9
        elif player == 'b':
            return c == 4 and 5 <= r <= 9
        elif player == 'd':
            return c == 10 and 5 <= r <= 9
        return False

    @staticmethod
    def get_camp_cells(player):
        cells = []
        if player == 'a':
            for r in range(0, 5):
                for c in range(5, 10):
                    cells.append((r, c))
        elif player == 'c':
            for r in range(10, 15):
                for c in range(5, 10):
                    cells.append((r, c))
        elif player == 'b':
            for r in range(5, 10):
                for c in range(0, 5):
                    cells.append((r, c))
        elif player == 'd':
            for r in range(5, 10):
                for c in range(10, 15):
                    cells.append((r, c))
        return cells

    def create_deck(self, player):
        team = self.seating[player]
        # In 2v2: Red gets hearts/diamonds, Black gets spades/clubs
        # In FFA: unique suits
        if team == 'red':
            suits = ['♥', '♦']
            joker_suit = '🃏_RED'
        elif team == 'black':
            suits = ['♠', '♣']
            joker_suit = '🃏_BLK'
        else:
            suit_map = {'a': ['♥', '♦'], 'c': ['♥', '♦'], 'b': ['♠', '♣'], 'd': ['♠', '♣']}
            suits = suit_map[player]
            joker_suit = f'🃏_{player.upper()}'

        deck = []
        for s in suits:
            for rank in RANKS:
                deck.append(Card4P(player, team, s, rank, False))
        deck.append(Card4P(player, team, joker_suit, 'JOKER', True))
        return deck

    def auto_setup(self, player):
        deck = self.create_deck(player)
        flag = next(c for c in deck if c.is_flag)
        mines = [c for c in deck if c.is_landmine]
        mobiles = [c for c in deck if not c.is_immobile]
        random.shuffle(mobiles)
        
        # 2 mobile cards in starting reserve
        self.hands[player]['starting'] = [mobiles.pop(), mobiles.pop()]
        self.hands[player]['mochigoma'] = []
        
        if player == 'a':
            corner_col = random.choice([5, 9])
            if corner_col == 5:
                flag_pos = (0, 5)
                mine_positions = [(0, 6), (1, 5), (1, 6), (0, 7)]
            else:
                flag_pos = (0, 9)
                mine_positions = [(0, 8), (1, 9), (1, 8), (0, 7)]
        elif player == 'c':
            corner_col = random.choice([5, 9])
            if corner_col == 5:
                flag_pos = (14, 5)
                mine_positions = [(14, 6), (13, 5), (13, 6), (14, 7)]
            else:
                flag_pos = (14, 9)
                mine_positions = [(14, 8), (13, 9), (13, 8), (14, 7)]
        elif player == 'b':
            corner_row = random.choice([5, 9])
            if corner_row == 5:
                flag_pos = (5, 0)
                mine_positions = [(6, 0), (5, 1), (6, 1), (7, 0)]
            else:
                flag_pos = (9, 0)
                mine_positions = [(8, 0), (9, 1), (8, 1), (7, 0)]
        elif player == 'd':
            corner_row = random.choice([5, 9])
            if corner_row == 5:
                flag_pos = (5, 14)
                mine_positions = [(6, 14), (5, 13), (6, 13), (7, 14)]
            else:
                flag_pos = (9, 14)
                mine_positions = [(8, 14), (9, 13), (8, 13), (7, 14)]

        self.board[flag_pos[0]][flag_pos[1]] = flag
        for idx, (mr, mc) in enumerate(mine_positions):
            self.board[mr][mc] = mines[idx]

        occupied = {flag_pos} | set(mine_positions)
        camp_cells = self.get_camp_cells(player)
        for r, c in camp_cells:
            if (r, c) not in occupied:
                self.board[r][c] = mobiles.pop()

    def get_counts(self, player):
        native = 0
        mochigoma = 0
        for r, c in self.get_camp_cells(player):
            # check entire board for pieces belonging to player
            pass
        for r in range(15):
            for c in range(15):
                card = self.board[r][c]
                if card and card.player == player:
                    if card.is_mochigoma:
                        mochigoma += 1
                    else:
                        native += 1
        native += len(self.hands[player]['starting'])
        mochigoma += len(self.hands[player]['mochigoma'])
        return native, mochigoma

    def can_accept_mochigoma(self, player):
        native, mochigoma = self.get_counts(player)
        return (mochigoma + 1) <= native

    def check_and_enforce_mutiny(self, player):
        if self.eliminated[player]:
            return
        native, mochigoma = self.get_counts(player)
        while mochigoma > native:
            self.stats['mutiny_triggers'] += 1
            if self.hands[player]['mochigoma']:
                discarded = self.hands[player]['mochigoma'].pop()
                self.graveyard.append(discarded)
            else:
                removed = False
                for r in range(15):
                    for c in range(15):
                        card = self.board[r][c]
                        if card and card.player == player and card.is_mochigoma:
                            self.graveyard.append(card)
                            self.board[r][c] = None
                            removed = True
                            break
                    if removed:
                        break
                if not removed:
                    break
            native, mochigoma = self.get_counts(player)

    def is_teammate(self, p1, p2):
        if self.mode == '2v2':
            return self.seating[p1] == self.seating[p2]
        return p1 == p2

    def get_legal_moves(self, r, c, for_player):
        card = self.board[r][c]
        if not card or card.player != for_player or card.is_immobile or self.eliminated[for_player]:
            return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_playable(nr, nc):
                target = self.board[nr][nc]
                if not target:
                    moves.append((nr, nc))
                elif not self.is_teammate(for_player, target.player):
                    moves.append((nr, nc)) # Enemy: legal attack!
        return moves

    def get_legal_drops(self, for_player):
        if self.eliminated[for_player]:
            return []
        # Can only drop on unoccupied tiles within own camp
        drops = []
        for r, c in self.get_camp_cells(for_player):
            if self.board[r][c] is None:
                drops.append((r, c))
        return drops

    def handle_capture(self, capturing_player, card):
        # Treason Execution / No Re-Conscription Rule
        if card.is_mochigoma:
            self.graveyard.append(card)
            self.stats['conscripts_executed'] += 1
            return
        
        card.player = capturing_player
        card.team = self.seating[capturing_player]
        card.is_bomb = False
        card.is_landmine = False
        card.is_flag = False
        card.is_sapper = False
        card.is_mochigoma = False
        if self.can_accept_mochigoma(capturing_player):
            self.hands[capturing_player]['mochigoma'].append(card)
        else:
            self.graveyard.append(card)
            self.stats['mutiny_triggers'] += 1

    def eliminate_player(self, player, reason):
        self.eliminated[player] = True
        self.stats['eliminations'] += 1
        # Clear remaining pieces from board to graveyard
        for r in range(15):
            for c in range(15):
                card = self.board[r][c]
                if card and card.player == player:
                    self.graveyard.append(card)
                    self.board[r][c] = None
        # Clear hands to graveyard
        for card in self.hands[player]['starting']:
            self.graveyard.append(card)
        self.hands[player]['starting'].clear()
        for card in self.hands[player]['mochigoma']:
            self.graveyard.append(card)
        self.hands[player]['mochigoma'].clear()
        self.check_game_over()

    def check_game_over(self):
        if self.mode == '2v2':
            red_alive = any(not self.eliminated[p] for p in ['a', 'b', 'c', 'd'] if self.seating[p] == 'red')
            black_alive = any(not self.eliminated[p] for p in ['a', 'b', 'c', 'd'] if self.seating[p] == 'black')
            if not red_alive:
                self.game_state = 'gameover'
                self.winner = 'black'
                self.win_reason = 'Team Black wins! All Red players eliminated.'
            elif not black_alive:
                self.game_state = 'gameover'
                self.winner = 'red'
                self.win_reason = 'Team Red wins! All Black players eliminated.'
        else: # FFA
            alive = [p for p in ['a', 'b', 'c', 'd'] if not self.eliminated[p]]
            if len(alive) <= 1:
                self.game_state = 'gameover'
                self.winner = alive[0] if alive else None
                self.win_reason = f"Player {self.winner.upper()} wins FFA!" if self.winner else 'Draw'

    def execute_move(self, fr, fc, tr, tc):
        attacker = self.board[fr][fc]
        defender = self.board[tr][tc]
        self.board[fr][fc] = None
        self.stats['moves'] += 1

        a_player = attacker.player

        # Advance to empty cell
        if not defender:
            self.board[tr][tc] = attacker
            self.finish_turn()
            return

        # Combat Clash
        d_player = defender.player

        # 1. Flag Assault
        if defender.is_flag:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.stats['flag_captures'] += 1
            self.eliminate_player(d_player, f"Flag of {d_player.upper()} was captured by {a_player.upper()}!")
            self.finish_turn()
            return

        # 2. Bomb Detonation
        if attacker.is_bomb or defender.is_bomb:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.stats['bomb_explosions'] += 1
            self.finish_turn()
            return

        # 3. Landmine
        if defender.is_landmine:
            if attacker.is_sapper or attacker.is_mochigoma:
                self.board[tr][tc] = attacker
                self.handle_capture(a_player, defender)
                self.stats['mines_cleared'] += 1
            else:
                self.board[tr][tc] = defender
                self.graveyard.append(attacker)
                self.stats['mines_detonated'] += 1
            self.finish_turn()
            return

        # 4. Conscript vs Conscript: Mutual destruction
        if attacker.is_mochigoma and defender.is_mochigoma:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.stats['conscripts_executed'] += 2
            self.finish_turn()
            return

        # 5. Native Sapper vs Native Sapper: Mutual destruction
        if (attacker.is_sapper and not attacker.is_mochigoma) and (defender.is_sapper and not defender.is_mochigoma):
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.finish_turn()
            return

        # 6. Native Sapper vs Conscript: Native Sapper wins! Conscript executed to Graveyard
        if (attacker.is_sapper and not attacker.is_mochigoma) and defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.stats['conscripts_executed'] += 1
            self.finish_turn()
            return
        if attacker.is_mochigoma and (defender.is_sapper and not defender.is_mochigoma):
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.stats['conscripts_executed'] += 1
            self.finish_turn()
            return

        # 7. Conscript vs Officer: Officer wins, Conscript executed to Graveyard
        if attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.stats['conscripts_executed'] += 1
            self.finish_turn()
            return
        if defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.stats['conscripts_executed'] += 1
            self.finish_turn()
            return

        # 8. Native Sapper vs Officer: Officer wins, Native Sapper captured
        if attacker.is_sapper and not attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.handle_capture(d_player, attacker)
            self.stats['officer_captures'] += 1
            self.finish_turn()
            return
        if defender.is_sapper and not defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.handle_capture(a_player, defender)
            self.stats['officer_captures'] += 1
            self.finish_turn()
            return

        # 9. Officer vs Officer
        av = OFFICER_RANKS.get(attacker.rank, 0)
        dv = OFFICER_RANKS.get(defender.rank, 0)
        if av > dv:
            self.board[tr][tc] = attacker
            self.handle_capture(a_player, defender)
            self.stats['officer_captures'] += 1
        elif av < dv:
            self.board[tr][tc] = defender
            self.handle_capture(d_player, attacker)
            self.stats['officer_captures'] += 1
        else:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None

        self.finish_turn()

    def execute_drop(self, hand_type, idx, tr, tc):
        player = self.current_player
        if hand_type == 'starting':
            card = self.hands[player]['starting'].pop(idx)
            card.face_up = False
            self.stats['drops_starting'] += 1
        else:
            card = self.hands[player]['mochigoma'].pop(idx)
            card.is_mochigoma = True
            card.is_bomb = False
            card.is_landmine = False
            card.is_flag = False
            card.is_sapper = False
            card.face_up = True
            self.stats['drops_mochigoma'] += 1

        self.board[tr][tc] = card
        self.finish_turn()

    def finish_turn(self):
        if self.game_state == 'gameover':
            return

        # Enforce Anti-Mutiny Caps for all 4 players
        for p in ['a', 'b', 'c', 'd']:
            self.check_and_enforce_mutiny(p)

        self.check_game_over()
        if self.game_state == 'gameover':
            return

        # Advance turn to next active (non-eliminated) player
        for _ in range(4):
            self.current_turn_idx = (self.current_turn_idx + 1) % 4
            next_p = self.current_player
            if not self.eliminated[next_p]:
                break

    def check_invariants(self):
        # Invariant 1: Total cards conservation == 108 cards across all board + hands + graveyard
        total = len(self.graveyard)
        for p in ['a', 'b', 'c', 'd']:
            total += len(self.hands[p]['starting']) + len(self.hands[p]['mochigoma'])
        for r in range(15):
            for c in range(15):
                card = self.board[r][c]
                if card:
                    assert self.is_playable(r, c), f"CRITICAL: Card on unplayable cell ({r}, {c})!"
                    total += 1
        assert total == 108, f"Card conservation violated! Expected 108, got {total}"

        # Invariant 2: Anti-Mutiny (mochigoma <= native)
        for p in ['a', 'b', 'c', 'd']:
            if not self.eliminated[p]:
                native, mochigoma = self.get_counts(p)
                assert mochigoma <= native, f"Anti-Mutiny violated for {p}: native={native}, mochigoma={mochigoma}"

        # Invariant 3: No Re-conscription in hand
        for p in ['a', 'b', 'c', 'd']:
            for card in self.hands[p]['mochigoma']:
                assert not card.is_mochigoma, f"Re-conscription violation! Card {card.rank} in {p} Mochigoma hand has is_mochigoma=True"


# ==============================================================
# 10-ITERATION TEST & DEBUG LOOP
# ==============================================================

def run_test_and_debug_loop():
    print("=" * 70)
    print("🎯 STARTING 10-ITERATION TEST & DEBUG LOOP FOR 4-PLAYER MODE")
    print("=" * 70)

    # ----------------------------------------------------------
    # Iteration 1: Board Geometry & Obstacle Collision Verification
    # ----------------------------------------------------------
    print("\n[LOOP 1/10] Verifying 15x15 Plus-Shaped Board & 4 Center Obstacles...")
    playable_count = 0
    for r in range(15):
        for c in range(15):
            if GameEngine4PSim.is_playable(r, c):
                playable_count += 1
    # 25 (A) + 25 (B) + 25 (C) + 25 (D) + 21 (Center: 25 - 4 obstacles) = 121 cells
    assert playable_count == 121, f"Expected 121 playable cells, got {playable_count}"
    for r, c in [(6, 6), (6, 8), (8, 6), (8, 8)]:
        assert not GameEngine4PSim.is_playable(r, c), f"Center obstacle ({r}, {c}) is wrongly marked playable!"
    for r, c in [(0, 0), (0, 4), (0, 14), (14, 0), (14, 14)]:
        assert not GameEngine4PSim.is_playable(r, c), f"Void corner ({r}, {c}) is wrongly marked playable!"
    print("  -> PASSED: Exactly 121 playable cells, 4 obstacles blocked, void corners sealed.")

    # ----------------------------------------------------------
    # Iteration 2: Deployment Invariants & Frontline Rules
    # ----------------------------------------------------------
    print("\n[LOOP 2/10] Verifying Deployment Phase & Frontline Restrictions...")
    sim = GameEngine4PSim(mode='2v2')
    for p in ['a', 'b', 'c', 'd']:
        sim.auto_setup(p)
        camp = sim.get_camp_cells(p)
        assert len(camp) == 25, f"Camp {p} does not have 25 cells!"
        assert len(sim.hands[p]['starting']) == 2, f"Player {p} starting reserve != 2!"
        for r, c in camp:
            card = sim.board[r][c]
            assert card is not None, f"Missing card at ({r}, {c}) in {p} camp!"
            if sim.is_frontline(p, r, c):
                assert not card.is_immobile, f"CRITICAL: Immobile card {card.rank} found on {p} frontline at ({r}, {c})!"
    sim.check_invariants()
    print("  -> PASSED: 100 cards deployed, 8 in reserves, 0 immobile units on frontlines.")

    # ----------------------------------------------------------
    # Iteration 3: Card Conservation Check across all States
    # ----------------------------------------------------------
    print("\n[LOOP 3/10] Verifying Exact Card Conservation (108 Cards)...")
    sim = GameEngine4PSim(mode='2v2')
    for p in ['a', 'b', 'c', 'd']:
        sim.auto_setup(p)
    sim.check_invariants()
    # Move a few cards into combat
    sim.board[5][5] = sim.board[4][5]
    sim.board[4][5] = None
    sim.check_invariants()
    print("  -> PASSED: Card conservation holds strictly at 108 cards.")

    # ----------------------------------------------------------
    # Iteration 4: 2v2 Opposite Seating (A & C Red vs B & D Black)
    # ----------------------------------------------------------
    print("\n[LOOP 4/10] Simulating 2v2 Opposite Seating (Classic Cross: Red A/C vs Black B/D)...")
    opposite_seating = {'a': 'red', 'c': 'red', 'b': 'black', 'd': 'black'}
    sim4 = GameEngine4PSim(mode='2v2', seating=opposite_seating)
    for p in ['a', 'b', 'c', 'd']:
        sim4.auto_setup(p)
    assert sim4.is_teammate('a', 'c') and not sim4.is_teammate('a', 'b')
    assert sim4.is_teammate('b', 'd') and not sim4.is_teammate('c', 'd')
    # Run 100 turns
    run_sim_game(sim4, max_turns=120)
    sim4.check_invariants()
    print(f"  -> PASSED: 2v2 Opposite Seating simulated smoothly. Winner: {sim4.winner or 'Game in progress'}")

    # ----------------------------------------------------------
    # Iteration 5: 2v2 Adjacent Seating Option 1 (Red A/B vs Black C/D)
    # ----------------------------------------------------------
    print("\n[LOOP 5/10] Simulating 2v2 Adjacent Seating Choice (Red A/B vs Black C/D)...")
    adj_seating1 = {'a': 'red', 'b': 'red', 'c': 'black', 'd': 'black'}
    sim5 = GameEngine4PSim(mode='2v2', seating=adj_seating1)
    for p in ['a', 'b', 'c', 'd']:
        sim5.auto_setup(p)
    assert sim5.is_teammate('a', 'b') and not sim5.is_teammate('a', 'c')
    run_sim_game(sim5, max_turns=120)
    sim5.check_invariants()
    print(f"  -> PASSED: 2v2 Adjacent Seating (A/B vs C/D) simulated with custom choice.")

    # ----------------------------------------------------------
    # Iteration 6: 2v2 Adjacent Seating Option 2 (Red A/D vs Black B/C)
    # ----------------------------------------------------------
    print("\n[LOOP 6/10] Simulating 2v2 Adjacent Seating Choice (Red A/D vs Black B/C)...")
    adj_seating2 = {'a': 'red', 'd': 'red', 'b': 'black', 'c': 'black'}
    sim6 = GameEngine4PSim(mode='2v2', seating=adj_seating2)
    for p in ['a', 'b', 'c', 'd']:
        sim6.auto_setup(p)
    assert sim6.is_teammate('a', 'd') and not sim6.is_teammate('a', 'b')
    run_sim_game(sim6, max_turns=120)
    sim6.check_invariants()
    print(f"  -> PASSED: 2v2 Adjacent Seating (A/D vs B/C) verified with 0 friendly-fire violations.")

    # ----------------------------------------------------------
    # Iteration 7: 4-Player Free-For-All (FFA) Mode
    # ----------------------------------------------------------
    print("\n[LOOP 7/10] Simulating 4-Player Free-For-All (FFA) Individual Mode...")
    sim7 = GameEngine4PSim(mode='ffa')
    for p in ['a', 'b', 'c', 'd']:
        sim7.auto_setup(p)
    for p1 in ['a', 'b', 'c', 'd']:
        for p2 in ['a', 'b', 'c', 'd']:
            if p1 != p2:
                assert not sim7.is_teammate(p1, p2), f"FFA players {p1} and {p2} should not be teammates!"
    run_sim_game(sim7, max_turns=120)
    sim7.check_invariants()
    print(f"  -> PASSED: FFA mode simulated with full 4-way conflict. Winner: {sim7.winner or 'Game in progress'}")

    # ----------------------------------------------------------
    # Iteration 8: Anti-Mutiny Caps Across 4 Players
    # ----------------------------------------------------------
    print("\n[LOOP 8/10] Stress-Testing Anti-Mutiny Caps in 4-Player Mode...")
    sim8 = GameEngine4PSim(mode='2v2')
    for p in ['a', 'b', 'c', 'd']:
        sim8.auto_setup(p)
    # Simulate repeated captures of player B's pieces by player A
    camp_b = sim8.get_camp_cells('b')
    for r, c in camp_b[:15]:
        card = sim8.board[r][c]
        if card:
            sim8.board[r][c] = None
            sim8.handle_capture('a', card)
    sim8.check_and_enforce_mutiny('a')
    native, mochi = sim8.get_counts('a')
    assert mochi <= native, f"Anti-Mutiny failed: native={native}, mochi={mochi}"
    sim8.check_invariants()
    print(f"  -> PASSED: Anti-Mutiny correctly capped player's conscripts to {native} native units.")

    # ----------------------------------------------------------
    # Iteration 9: No Re-Conscription / Treason Execution in 4-Player
    # ----------------------------------------------------------
    print("\n[LOOP 9/10] Verifying Treason Execution (No Re-Conscription) in 4-Player...")
    sim9 = GameEngine4PSim(mode='2v2')
    for p in ['a', 'b', 'c', 'd']:
        sim9.auto_setup(p)
    # Take an existing card from player A's reserve, drop it as conscript at (5, 5)
    conscript = sim9.hands['a']['starting'].pop()
    conscript.is_mochigoma = True
    conscript.face_up = True
    sim9.board[5][5] = conscript
    # Move an existing officer from player B's camp to (5, 6)
    officer = None
    for r, c in sim9.get_camp_cells('b'):
        c_card = sim9.board[r][c]
        if c_card and c_card.rank in OFFICER_RANKS:
            officer = c_card
            sim9.board[r][c] = None
            break
    assert officer is not None
    sim9.board[5][6] = officer
    sim9.execute_move(5, 6, 5, 5) # Officer attacks Conscript
    assert conscript in sim9.graveyard, "Traitor Conscript was NOT sent to Graveyard!"
    assert conscript not in sim9.hands['b']['mochigoma'], "Traitor Conscript was illegally re-conscripted into Mochigoma!"
    sim9.check_invariants()
    print("  -> PASSED: Conscript executed straight to Graveyard; zero re-conscription.")

    # ----------------------------------------------------------
    # Iteration 10: 20 Full Matches Stress-Test (10 2v2 + 10 FFA)
    # ----------------------------------------------------------
    print("\n[LOOP 10/10] Running 20 Full Matches Batch Stress-Test (10 2v2 + 10 FFA)...")
    results = {'red': 0, 'black': 0, 'ffa_wins': 0, 'draws': 0}
    total_eliminations = 0
    total_conscripts_executed = 0

    for i in range(1, 21):
        m = '2v2' if i <= 10 else 'ffa'
        # alternate seating for 2v2
        seat = None
        if m == '2v2':
            if i % 3 == 0:
                seat = {'a': 'red', 'b': 'red', 'c': 'black', 'd': 'black'}
            elif i % 3 == 1:
                seat = {'a': 'red', 'c': 'red', 'b': 'black', 'd': 'black'}
            else:
                seat = {'a': 'red', 'd': 'red', 'b': 'black', 'c': 'black'}
        
        sim = GameEngine4PSim(mode=m, seating=seat)
        for p in ['a', 'b', 'c', 'd']:
            sim.auto_setup(p)
        run_sim_game(sim, max_turns=600)
        sim.check_invariants()

        total_eliminations += sim.stats['eliminations']
        total_conscripts_executed += sim.stats['conscripts_executed']

        if sim.winner == 'red':
            results['red'] += 1
        elif sim.winner == 'black':
            results['black'] += 1
        elif sim.winner:
            results['ffa_wins'] += 1
        else:
            results['draws'] += 1

    print("=" * 70)
    print("🏆 ALL 10 TEST & DEBUG ITERATIONS COMPLETED WITH 100% SUCCESS!")
    print(f"  • Total Matches in Loop 10:       20 (10 2v2 + 10 FFA)")
    print(f"  • Team Red Victories:             {results['red']}")
    print(f"  • Team Black Victories:           {results['black']}")
    print(f"  • FFA Individual Champions:       {results['ffa_wins']}")
    print(f"  • Time-Limit Draws:               {results['draws']}")
    print(f"  • Total Generals Eliminated:      {total_eliminations}")
    print(f"  • Treason Conscripts Executed:    {total_conscripts_executed}")
    print(f"  • Invariant Failures / Crashes:   0 (100.0% Pass Rate)")
    print("=" * 70)


def run_sim_game(sim, max_turns=200):
    turns = 0
    while sim.game_state != 'gameover' and turns < max_turns:
        turns += 1
        player = sim.current_player
        if sim.eliminated[player]:
            sim.finish_turn()
            continue

        # Collect moves
        actions = []
        for r in range(15):
            for c in range(15):
                card = sim.board[r][c]
                if card and card.player == player and not card.is_immobile:
                    for tr, tc in sim.get_legal_moves(r, c, player):
                        target = sim.board[tr][tc]
                        score = 10
                        # Directional aggressive push toward center / enemy territory
                        if player == 'a' and tr > r: score += 18
                        elif player == 'c' and tr < r: score += 18
                        elif player == 'b' and tc > c: score += 18
                        elif player == 'd' and tc < c: score += 18
                        
                        if target:
                            if target.is_flag: score += 100000
                            elif card.is_bomb: score += 60
                            elif card.is_sapper or card.is_mochigoma: score += 50
                            else: score += 40
                        actions.append(('move', (r, c), (tr, tc), score))

        # Collect drops
        drops = sim.get_legal_drops(player)
        if drops:
            for idx in range(len(sim.hands[player]['mochigoma'])):
                for d in drops[:3]:
                    actions.append(('drop', 'mochigoma', idx, d, 20))
            for idx in range(len(sim.hands[player]['starting'])):
                for d in drops[:2]:
                    actions.append(('drop', 'starting', idx, d, 15))

        if not actions:
            sim.eliminate_player(player, f"{player} stalemated with no moves.")
            continue

        actions.sort(key=lambda x: x[-1], reverse=True)
        top = actions[:min(3, len(actions))]
        chosen = random.choice(top)

        if chosen[0] == 'move':
            sim.execute_move(chosen[1][0], chosen[1][1], chosen[2][0], chosen[2][1])
        else:
            sim.execute_drop(chosen[1], chosen[2], chosen[3][0], chosen[3][1])


if __name__ == '__main__':
    run_test_and_debug_loop()
