# 1,000-Game Comprehensive Verification Suite for Poker Shogi & Junqi
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
        
        self.stats = {
            'moves': 0,
            'drops_starting': 0,
            'drops_mochigoma': 0,
            'flag_captures': 0,
            'bomb_explosions': 0,
            'mines_cleared': 0,
            'mines_detonated': 0,
            'officer_captures': 0,
            'mutiny_triggers': 0,
            'repetitions': 0
        }

    def reset_for_new_game(self):
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

    def create_deck(self, player):
        deck = []
        for suit in SUITS[player]:
            for rank in RANKS:
                deck.append(Card(player, suit, rank, False))
        deck.append(Card(player, '🃏', 'JOKER', True))
        return deck

    def auto_setup(self, player):
        deck = self.create_deck(player)
        random.shuffle(deck)
        
        self.hands[player]['starting'] = [deck.pop(), deck.pop()]
        
        immobile = [c for c in deck if c.is_immobile]
        mobile = [c for c in deck if not c.is_immobile]
        
        front_row = 4 if player == 'red' else 7
        camp_rows = [0, 1, 2, 3, 4] if player == 'red' else [11, 10, 9, 8, 7]
        
        front_pos = [(front_row, c) for c in range(5)]
        back_pos = [(r, c) for r in camp_rows if r != front_row for c in range(5)]
        
        # Invariant: NO Flag or Mines on frontline
        for r, c in front_pos:
            c_card = mobile.pop()
            assert not c_card.is_immobile, "Frontline violation!"
            self.board[r][c] = c_card
        
        remainder = immobile + mobile
        for r, c in back_pos:
            self.board[r][c] = remainder.pop()

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
            if self.hands[player]['mochigoma']:
                discarded = self.hands[player]['mochigoma'].pop()
                self.graveyard.append(discarded)
            else:
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
        card.player = capturing_player
        native, mochigoma = self.get_counts(capturing_player)
        if (mochigoma + 1) <= native:
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
        assert not attacker.is_immobile, "Immobile card moved!"
        self.board[fr][fc] = None
        self.stats['moves'] += 1

        if not defender:
            self.board[tr][tc] = attacker
            self.finish_turn()
            return

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
            self.position_counts.clear()
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
            self.position_counts.clear()
            self.finish_turn()
            return

        # 4. Sapper vs Sapper
        if (attacker.is_sapper or attacker.is_mochigoma) and (defender.is_sapper or defender.is_mochigoma):
            self.graveyard.extend([attacker, defender])
            self.board[tr][tc] = None
            self.position_counts.clear()
            self.finish_turn()
            return

        # 5. Sapper vs Officer
        if attacker.is_sapper or attacker.is_mochigoma:
            self.board[tr][tc] = defender
            self.handle_capture(d_player, attacker)
            self.stats['officer_captures'] += 1
            self.position_counts.clear()
            self.finish_turn()
            return

        if defender.is_sapper or defender.is_mochigoma:
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
        min_r = 0 if player == 'red' else 7
        max_r = 4 if player == 'red' else 11
        assert min_r <= tr <= max_r, "Drop out of camp bounds!"
        assert self.board[tr][tc] is None, "Drop on occupied square!"

        if hand_type == 'starting':
            card = self.hands[player]['starting'].pop(idx)
            card.face_up = False
            self.stats['drops_starting'] += 1
        else:
            card = self.hands[player]['mochigoma'].pop(idx)
            card.is_mochigoma = True
            card.face_up = True
            self.stats['drops_mochigoma'] += 1

        self.board[tr][tc] = card
        self.position_counts.clear()
        self.finish_turn()

    def finish_turn(self):
        if self.game_state == 'gameover':
            return

        self.check_and_enforce_mutiny('red')
        self.check_and_enforce_mutiny('black')

        self.current_turn = 'black' if self.current_turn == 'red' else 'red'

        h = self.get_hash()
        self.position_counts[h] = self.position_counts.get(h, 0) + 1
        if self.position_counts[h] >= 3:
            self.stats['repetitions'] += 1
            self.end_game(None, 'DRAW: Threefold repetition.')
            return

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
        self.check_and_enforce_mutiny('red')
        self.check_and_enforce_mutiny('black')

    def check_invariants(self):
        # 1. Anti-Mutiny Invariant
        for p in ['red', 'black']:
            native, mochigoma = self.get_counts(p)
            assert mochigoma <= native, f"CRITICAL: Anti-Mutiny violated for {p}! Native: {native}, Mochigoma: {mochigoma}"

        # 2. Total 54 Cards Conservation Invariant
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
    sim.reset_for_new_game()
    sim.auto_setup('red')
    sim.auto_setup('black')
    sim.check_invariants()

    turn_limit = 400
    turns = 0

    while sim.game_state == 'playing' and turns < turn_limit:
        turns += 1
        player = sim.current_turn

        actions = []
        for r in range(12):
            for c in range(5):
                card = sim.board[r][c]
                if card and card.player == player and not card.is_immobile:
                    for tr, tc in sim.get_legal_moves(r, c, player):
                        target = sim.board[tr][tc]
                        score = 10
                        if player == 'red' and tr > r: score += 12
                        if player == 'black' and tr < r: score += 12
                        if target:
                            if target.is_flag: score += 10000
                            elif card.is_bomb: score += 45
                            elif card.is_sapper or card.is_mochigoma: score += 35
                            else: score += 25
                        actions.append(('move', (r, c), (tr, tc), score))

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

        actions.sort(key=lambda x: x[-1], reverse=True)
        top = actions[:min(3, len(actions))]
        chosen = random.choice(top)

        if chosen[0] == 'move':
            sim.execute_move(chosen[1][0], chosen[1][1], chosen[2][0], chosen[2][1])
        else:
            sim.execute_drop(chosen[1], chosen[2], chosen[3][0], chosen[3][1])

        sim.check_invariants()

    if turns >= turn_limit and sim.game_state == 'playing':
        sim.end_game(None, 'Turn limit reached (400 moves)')

    return sim

def main():
    print("=" * 65)
    print("🚀 RUNNING 1,000-GAME EXHAUSTIVE STRESS TEST FOR POKER SHOGI & JUNQI")
    print("=" * 65)

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
        'mutiny_triggers': 0,
        'repetitions': 0
    }

    for i in range(1, 1001):
        game = run_one_game(i)
        winner = game.winner if game.winner else 'draw'
        results[winner] += 1
        
        reason_cat = 'Flag Assassination' if 'Flag' in game.win_reason else \
                     ('Repetition Draw' if 'repetition' in game.win_reason else \
                     ('Stalemate/Extinction' if 'stalemate' in game.win_reason.lower() or 'moves' in game.win_reason.lower() else 'Turn Limit'))
        reasons[reason_cat] = reasons.get(reason_cat, 0) + 1

        for k in aggregated_stats:
            aggregated_stats[k] += game.stats[k if k != 'total_moves' else 'moves']

        if i % 100 == 0:
            print(f"  -> Games 1 to {i:<4} PASSED 100% of invariants (Board: 54 cards, Mutiny <= Native).")

    print("\n" + "=" * 65)
    print("🎯 1,000-GAME STRESS TEST RESULTS & METRICS REPORT")
    print("=" * 65)
    print(f"Total Games Played:        1,000")
    print(f"Completed Without Crashes: 1,000 (100.0%)")
    print(f"Red Victories:             {results['red']} ({results['red']/10:.1f}%)")
    print(f"Black Victories:           {results['black']} ({results['black']/10:.1f}%)")
    print(f"Draws:                     {results['draw']} ({results['draw']/10:.1f}%)")
    print("-" * 65)
    print("Outcome Distribution:")
    for cat, count in reasons.items():
        print(f"  • {cat:<24}: {count:>4} games ({count/10:.1f}%)")
    print("-" * 65)
    print("Mechanisms Tested Across 1,000 Games:")
    print(f"  • Total Piece Advances:    {aggregated_stats['total_moves']} moves")
    print(f"  • Flag Assassinations:     {aggregated_stats['flag_captures']}")
    print(f"  • Officer Combat Clashes:  {aggregated_stats['officer_captures']}")
    print(f"  • Bomb (King) Explosions:  {aggregated_stats['bomb_explosions']}")
    print(f"  • Landmines Cleared:       {aggregated_stats['mines_cleared']}")
    print(f"  • Non-Sapper Mine Deaths:  {aggregated_stats['mines_detonated']}")
    print(f"  • Starting Reserve Drops:  {aggregated_stats['drops_starting']}")
    print(f"  • Mochigoma Sapper Drops:  {aggregated_stats['drops_mochigoma']}")
    print(f"  • Anti-Mutiny Graveyard:   {aggregated_stats['mutiny_triggers']} prisoners disbanded")
    print(f"  • Repetition Draws:        {aggregated_stats['repetitions']}")
    print("=" * 65)
    print("✅ ALL 1,000 GAMES COMPLETED AND 100% OF INVARIANTS MET!")
    print("=" * 65)

if __name__ == "__main__":
    main()
