from game import Action


class Player:
    name = "player"

    def __init__(self, game, player):
        self.game = game
        self.player = player

    def legal_actions(self):
        return self.game.legal_actions(self.player)

    def position(self):
        return self.game.player_positions[self.player]

    def target_is_slimy(self, tile):
        return self.game.is_slimy(tile)


class RandomPlayer(Player):
    name = "random"

    def choose_action(self):
        return self.game.rng.choice(self.legal_actions())


class CautiousPlayer(Player):
    name = "cautious"

    def choose_action(self):
        legal = self.legal_actions()
        if Action.JUMP not in legal:
            return Action.STAY
        if self.target_is_slimy(self.position() + 1):
            return Action.STAY
        return Action.JUMP


class AggressivePlayer(Player):
    name = "aggressive"

    def choose_action(self):
        legal = self.legal_actions()
        if Action.LONG_JUMP in legal:
            return Action.LONG_JUMP
        if Action.JUMP in legal:
            return Action.JUMP
        return Action.STAY


class BalancedPlayer(Player):
    name = "balanced"

    def choose_action(self):
        legal = self.legal_actions()
        position = self.position()
        if Action.LONG_JUMP in legal and not self.target_is_slimy(position + 2):
            return Action.LONG_JUMP
        if Action.JUMP in legal:
            return Action.JUMP
        return Action.STAY


DUMMY_PLAYERS = {
    "random": RandomPlayer,
    "cautious": CautiousPlayer,
    "aggressive": AggressivePlayer,
    "balanced": BalancedPlayer,
}


def make_dummy_player(name, game, player):
    return DUMMY_PLAYERS[name](game, player)
