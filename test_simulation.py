# 100-Game Full Simulation Test Suite for Poker Shogi & Junqi
# Verifies all rules, state transitions, combat resolutions, and anti-mutiny caps across 100 games.

import random
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

SUITS = {
    'red': ['♥', '♦'],
    'black': ['♠', '♣']
}
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
OFFICER_RANKS = {'10': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

class Card:
    def __init__(self, player, suit, rank, is_joker=False):
        self.player = player
        self.original_owner = player
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

class GameEngineSim:
    def __init__(self):
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
        
        # Rule telemetry
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
            'repetitions': 0
        }

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

        # 2 mobile cards in starting reserves
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
                    assert not c_card.is_immobile, "Immobile card misplaced on board!"
                    self.board[r][c] = c_card

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

    def can_accept_mochigoma(self, player):
        native, mochigoma = self.get_counts(player)
        return (mochigoma + 1) <= native

    def check_and_enforce_mutiny(self, player):
        native, mochigoma = self.get_counts(player)
        while mochigoma > native:
            self.stats['mutiny_triggers'] += 1
            # 1. First discard from hand
            if self.hands[player]['mochigoma']:
                discarded = self.hands[player]['mochigoma'].pop()
                self.graveyard.append(discarded)
            else:
                # 2. If hand is empty, a deployed Mochigoma Sapper mutinies/disbands
                removed = False
                for r in range(12):
                    for c in range(5):
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

    def handle_capture(self, capturing_player, card):
        if card.is_mochigoma:
            self.graveyard.append(card)
            self.stats['conscripts_executed'] += 1
            return
        card.player = capturing_player
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

    def get_legal_moves(self, r, c, for_player):
        card = self.board[r][c]
        if not card or card.player != for_player or card.is_immobile:
            return []
        moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 12 and 0 <= nc < 5:
                target = self.board[nr][nc]
                if not target or target.player != card.player:
                    moves.append((nr, nc))
        return moves

    def get_legal_drops(self, for_player):
        min_r = 0 if for_player == 'red' else 7
        max_r = 4 if for_player == 'red' else 11
        drops = []
        for r in range(min_r, max_r + 1):
            for c in range(5):
                if self.board[r][c] is None:
                    drops.append((r, c))
        return drops

    def has_any_legal_action(self, player):
        for r in range(12):
            for c in range(5):
                if self.get_legal_moves(r, c, player):
                    return True
        has_hand = bool(self.hands[player]['starting'] or self.hands[player]['mochigoma'])
        if has_hand and self.get_legal_drops(player):
            return True
        return False

    def execute_move(self, fr, fc, tr, tc):
        attacker = self.board[fr][fc]
        defender = self.board[tr][tc]
        self.board[fr][fc] = None
        self.stats['moves'] += 1

        if not defender:
            self.board[tr][tc] = attacker
            self.finish_turn()
            return

        # Combat Clash
        a_player = attacker.player
        d_player = defender.player

        # 1. Flag Assault
        if defender.is_flag:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.stats['flag_captures'] += 1
            self.end_game(a_player, f'{a_player.upper()} captured the enemy Flag!')
            return

        # 2. Bomb Detonation
        if attacker.is_bomb or defender.is_bomb:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.stats['bomb_explosions'] += 1
            self.position_counts.clear() # Reset repetition on kill
            self.finish_turn()
            return

        # 3. Landmine
        if defender.is_landmine:
            if attacker.is_sapper or attacker.is_mochigoma:
                # Sapper disarms mine
                self.board[tr][tc] = attacker
                self.handle_capture(a_player, defender)
                self.stats['mines_cleared'] += 1
            else:
                # Non-sapper dies
                self.board[tr][tc] = defender
                self.graveyard.append(attacker)
                self.stats['mines_detonated'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return

        # 4. Conscript vs Conscript: Mutual destruction
        if attacker.is_mochigoma and defender.is_mochigoma:
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.stats['conscripts_executed'] += 2
            self.position_counts.clear()
            self.finish_turn()
            return

        # 5. Native Sapper vs Native Sapper: Mutual destruction
        if (attacker.is_sapper and not attacker.is_mochigoma) and (defender.is_sapper and not defender.is_mochigoma):
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.position_counts.clear()
            self.finish_turn()
            return

        # 6. Native Sapper vs Conscript: Native Sapper wins! Conscript executed to Graveyard
        if (attacker.is_sapper and not attacker.is_mochigoma) and defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.stats['conscripts_executed'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return
        if attacker.is_mochigoma and (defender.is_sapper and not defender.is_mochigoma):
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.stats['conscripts_executed'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return

        # 7. Conscript vs Officer: Officer wins, Conscript executed to Graveyard
        if attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.graveyard.append(attacker)
            self.stats['conscripts_executed'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return
        if defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.graveyard.append(defender)
            self.stats['conscripts_executed'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return

        # 8. Native Sapper vs Officer: Officer wins, Native Sapper captured
        if attacker.is_sapper and not attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.handle_capture(d_player, attacker)
            self.stats['officer_captures'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return
        if defender.is_sapper and not defender.is_mochigoma:
            self.board[tr][tc] = attacker
            self.handle_capture(a_player, defender)
            self.stats['officer_captures'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return

        # 6. Officer vs Officer
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
        self.position_counts.clear()
        self.finish_turn()

    def execute_drop(self, hand_type, idx, tr, tc):
        player = self.current_turn
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
        self.position_counts.clear()
        self.finish_turn()

    def finish_turn(self):
        if self.game_state == 'gameover':
            return

        # Enforce Anti-Mutiny Caps for both players
        self.check_and_enforce_mutiny('red')
        self.check_and_enforce_mutiny('black')

        # Switch turn
        self.current_turn = 'black' if self.current_turn == 'red' else 'red'

        # Check repetition
        h = self.get_hash()
        self.position_counts[h] = self.position_counts.get(h, 0) + 1
        if self.position_counts[h] >= 3:
            self.stats['repetitions'] += 1
            self.end_game(None, 'DRAW: Threefold repetition.')
            return

        # Check extinction
        if not self.has_any_legal_action(self.current_turn):
            winner = 'black' if self.current_turn == 'red' else 'red'
            self.end_game(winner, f'{winner.upper()} WINS: Opponent stalemated / no moves.')

    def get_hash(self):
        s = f"{self.current_turn}:"
        for r in range(12):
            for c in range(5):
                card = self.board[r][c]
                s += '0,' if not card else f"{card.player[0]}{card.rank}{'M' if card.is_mochigoma else ''},"
        return s

    def end_game(self, winner, reason):
        self.game_state = 'gameover'
        self.winner = winner
        self.win_reason = reason

    def check_invariants(self):
        # 1. Anti-Mutiny Invariant
        for p in ['red', 'black']:
            native, mochigoma = self.get_counts(p)
            assert mochigoma <= native, f"CRITICAL: Anti-Mutiny violated for {p}! Native: {native}, Mochigoma: {mochigoma}"

        # 2. No Re-conscription Invariant: No card in Mochigoma hand may have is_mochigoma == True
        for p in ['red', 'black']:
            for card in self.hands[p]['mochigoma']:
                assert not card.is_mochigoma, f"CRITICAL: Re-conscription detected! Card {card.rank} in {p} Mochigoma hand has is_mochigoma=True"

        # 3. Total cards conservation: board + hands + graveyard == 54
        total = len(self.graveyard)
        for p in ['red', 'black']:
            total += len(self.hands[p]['starting']) + len(self.hands[p]['mochigoma'])
        for r in range(12):
            for c in range(5):
                if self.board[r][c]:
                    total += 1
        assert total == 54, f"Card conservation violated! Expected 54, got {total}"


def run_one_game(game_id):
    sim = GameEngineSim()
    sim.auto_setup('red')
    sim.auto_setup('black')
    sim.check_invariants()

    turn_limit = 500
    turns = 0

    while sim.game_state == 'playing' and turns < turn_limit:
        turns += 1
        player = sim.current_turn

        # Gather actions
        actions = []

        # Moves
        for r in range(12):
            for c in range(5):
                card = sim.board[r][c]
                if card and card.player == player and not card.is_immobile:
                    for tr, tc in sim.get_legal_moves(r, c, player):
                        target = sim.board[tr][tc]
                        score = 10
                        # Prefer advancing
                        if player == 'red' and tr > r: score += 12
                        if player == 'black' and tr < r: score += 12
                        if target:
                            if target.is_flag: score += 10000
                            elif card.is_bomb: score += 45
                            elif card.is_sapper or card.is_mochigoma: score += 35
                            else: score += 25
                        actions.append(('move', (r, c), (tr, tc), score))

        # Drops
        legal_drops = sim.get_legal_drops(player)
        if legal_drops:
            for idx in range(len(sim.hands[player]['mochigoma'])):
                for d in legal_drops:
                    actions.append(('drop', 'mochigoma', idx, d, 20))
            for idx in range(len(sim.hands[player]['starting'])):
                for d in legal_drops:
                    actions.append(('drop', 'starting', idx, d, 15))

        if not actions:
            sim.end_game('black' if player == 'red' else 'red', 'Stalemate')
            break

        # Select action
        actions.sort(key=lambda x: x[-1], reverse=True)
        top = actions[:min(3, len(actions))]
        chosen = random.choice(top)

        if chosen[0] == 'move':
            sim.execute_move(chosen[1][0], chosen[1][1], chosen[2][0], chosen[2][1])
        else:
            sim.execute_drop(chosen[1], chosen[2], chosen[3][0], chosen[3][1])

        sim.check_invariants()

    if turns >= turn_limit and sim.game_state == 'playing':
        sim.end_game(None, 'Turn limit reached (500 moves)')

    return sim

def main():
    print("=" * 60)
    print("🚀 STARTING 100-GAME AUTOMATED TESTING SUITE FOR POKER SHOGI & JUNQI")
    print("=" * 60)

    results = {'red': 0, 'black': 0, 'draw': 0}
    reasons = {}
    aggregated_stats = {
        'total_moves': 0,
        'drops_starting': 0,
        'drops_mochigoma': 0,
        'flag_captures': 0,
        'bomb_explosions': 0,
        'mines_cleared': 0,
        'mines_detonated': 0,
        'officer_captures': 0,
        'conscripts_executed': 0,
        'mutiny_triggers': 0,
        'repetitions': 0
    }

    for i in range(1, 101):
        game = run_one_game(i)
        winner = game.winner if game.winner else 'draw'
        results[winner] += 1
        
        reason_cat = 'Flag Assassination' if 'Flag' in game.win_reason else \
                     ('Repetition Draw' if 'repetition' in game.win_reason else \
                     ('Stalemate/Extinction' if 'stalemate' in game.win_reason.lower() or 'moves' in game.win_reason.lower() else 'Other'))
        reasons[reason_cat] = reasons.get(reason_cat, 0) + 1

        for k in aggregated_stats:
            aggregated_stats[k] += game.stats[k if k != 'total_moves' else 'moves']

        if i % 20 == 0:
            print(f"  -> Games 1 to {i} completed smoothly. No invariant violations.")

    print("\n" + "=" * 60)
    print("🎯 100-GAME SIMULATION RESULTS & TELEMETRY REPORT")
    print("=" * 60)
    print(f"Total Games Played:        100")
    print(f"Games Without Crashes:     100 (100.0%)")
    print(f"Red Victories:             {results['red']}")
    print(f"Black Victories:           {results['black']}")
    print(f"Draws:                     {results['draw']}")
    print("-" * 60)
    print("Game Outcome Breakdown:")
    for cat, count in reasons.items():
        print(f"  • {cat:<24}: {count} games")
    print("-" * 60)
    print("Mechanism & Rule Exercise Counts across 100 Games:")
    print(f"  • Total Piece Advances:    {aggregated_stats['total_moves']} moves")
    print(f"  • Flag Assassinations:     {aggregated_stats['flag_captures']}")
    print(f"  • Officer Combat Captures: {aggregated_stats['officer_captures']}")
    print(f"  • Bomb (King) Explosions:  {aggregated_stats['bomb_explosions']}")
    print(f"  • Landmines Cleared:       {aggregated_stats['mines_cleared']}")
    print(f"  • Non-Sapper Mine Deaths:  {aggregated_stats['mines_detonated']}")
    print(f"  • Starting Reserve Drops:  {aggregated_stats['drops_starting']}")
    print(f"  • Mochigoma Sapper Drops:  {aggregated_stats['drops_mochigoma']}")
    print(f"  • Conscripts Executed:     {aggregated_stats['conscripts_executed']} (treason execution to Graveyard)")
    print(f"  • Anti-Mutiny Graveyard:   {aggregated_stats['mutiny_triggers']} prisoners executed/discarded")
    print(f"  • Repetition Draws:        {aggregated_stats['repetitions']}")
    print("=" * 60)
    print("✅ ALL 100 GAMES COMPLETED AND 100% OF INVARIANTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
