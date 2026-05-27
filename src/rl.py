import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from dummy_players import Player, DUMMY_PLAYERS, make_dummy_player
from game import Action, Game


ACTIONS = tuple(Action)
MIXED_OPPONENTS = ("random", "cautious", "aggressive")
TRAINING_OPPONENTS = ("mixed", *DUMMY_PLAYERS)


@dataclass(frozen=True)
class RewardConfig:
    win: float = 5.0
    loss: float = -3.0
    step: float = -0.04
    progress: float = 0.15
    fall: float = -0.02


@dataclass(frozen=True)
class TrainingConfig:
    episodes: int = 20_000
    alpha: float = 0.15
    gamma: float = 0.90
    epsilon_start: float = 0.30
    epsilon_end: float = 0.02
    epsilon_decay: float = 0.9995
    seed: int = 42
    track_length: int = 10
    opponent: str = "mixed"


def action_key(action):
    return action.name


def empty_values():
    return {action_key(action): 0.0 for action in ACTIONS}


def state_key(game, player):
    other = 1 - player
    parts = [str(game.player_positions[player]), str(game.player_positions[other])]
    for current_player in (player, other):
        position = game.player_positions[current_player]
        targets = (
            min(position + Action.JUMP.jump_distance, game.goal_tile),
            min(position + Action.LONG_JUMP.jump_distance, game.goal_tile),
        )
        parts.extend("1" if game.is_slimy(tile) else "0" for tile in targets)
    return "|".join(parts)


def fell(game, action, old_position, new_position):
    target = min(old_position + action.jump_distance, game.goal_tile)
    return action is not Action.STAY and target != 0 and new_position == 0


class QLearningPlayer(Player):
    name = "q_learning"

    def __init__(self, game, player_idx, q_table=None, epsilon=0.0):
        super().__init__(game, player_idx)
        self.q_table = q_table or {}
        self.epsilon = epsilon
        self.alpha = 0.15
        self.gamma = 0.90

    def values(self, key, create=True):
        if key not in self.q_table and create:
            self.q_table[key] = empty_values()
        return self.q_table.get(key, empty_values())

    def choose_action(self, explore=False):
        legal = self.game.legal_actions(self.player_idx)
        if explore and self.game.rng.random() < self.epsilon:
            return self.game.rng.choice(legal)
        values = self.values(state_key(self.game, self.player_idx), create=explore)
        best = max(values[action_key(action)] for action in legal)
        return self.game.rng.choice([action for action in legal if values[action_key(action)] == best])

    def update(self, key, action, reward, next_key, next_actions):
        values = self.values(key)
        old = values[action_key(action)]
        target = reward
        if next_key is not None:
            next_values = self.values(next_key)
            target += self.gamma * max(next_values[action_key(action)] for action in next_actions)
        values[action_key(action)] = old + self.alpha * (target - old)

    def copy_for(self, game, player):
        clone = QLearningPlayer(game, player, self.q_table, self.epsilon)
        if hasattr(self, "alpha"):
            clone.alpha = self.alpha
            clone.gamma = self.gamma
        return clone


def reward_for_round(game, rewards, old_position, action, winner):
    if winner == 0:
        return rewards.win
    if winner == 1:
        return rewards.loss
    new_position = game.player_positions[0]
    reward = rewards.step + max(0, new_position - old_position) * rewards.progress
    if fell(game, action, old_position, new_position):
        reward += rewards.fall
    return reward


def train(config=None, rewards=None):
    config = config or TrainingConfig()
    rewards = rewards or RewardConfig()
    q_table = {}
    epsilon = config.epsilon_start
    stats = {"wins": 0, "losses": 0}

    for episode in range(config.episodes):
        game = Game(config.track_length, config.seed + episode)
        learner = QLearningPlayer(game, 0, q_table, epsilon)
        learner.alpha = config.alpha
        learner.gamma = config.gamma
        opponent_name = config.opponent
        if opponent_name == "mixed":
            opponent_name = game.rng.choice(MIXED_OPPONENTS)
        opponent = make_dummy_player(opponent_name, game, 1)

        while game.winner is None:
            key = state_key(game, 0)
            old_position = game.player_positions[0]
            action = learner.choose_action(explore=True)
            game.apply_action(0, action)
            if game.winner is None:
                game.apply_action(1, opponent.choose_action())
            if game.winner is None:
                game.flip_tiles()

            reward = reward_for_round(game, rewards, old_position, action, game.winner)
            next_key = None if game.winner is not None else state_key(game, 0)
            next_actions = () if next_key is None else game.legal_actions(0)
            learner.update(key, action, reward, next_key, next_actions)

        stats["wins"] += int(game.winner == 0)
        stats["losses"] += int(game.winner == 1)
        epsilon = max(config.epsilon_end, epsilon * config.epsilon_decay)

    return QLearningPlayer(None, 0, q_table, config.epsilon_end), stats


def evaluate(player, games=1000, track_length=10, opponent_name="balanced", seed=1000):
    wins = losses = 0
    for i in range(games):
        game = Game(track_length, seed + i)
        learner = player.copy_for(game, 0)
        opponent = make_dummy_player(opponent_name, game, 1)
        while game.winner is None:
            game.apply_action(0, learner.choose_action())
            if game.winner is None:
                game.apply_action(1, opponent.choose_action())
            if game.winner is None:
                game.flip_tiles()
        wins += int(game.winner == 0)
        losses += int(game.winner == 1)
    return {"games": games, "wins": wins, "losses": losses, "win_rate": wins / games}


def evaluate_dummy(player_name, games=1000, track_length=10, opponent_name="balanced", seed=1000):
    wins = losses = 0
    for i in range(games):
        game = Game(track_length, seed + i)
        player = make_dummy_player(player_name, game, 0)
        opponent = make_dummy_player(opponent_name, game, 1)
        while game.winner is None:
            game.apply_action(0, player.choose_action())
            if game.winner is None:
                game.apply_action(1, opponent.choose_action())
            if game.winner is None:
                game.flip_tiles()
        wins += int(game.winner == 0)
        losses += int(game.winner == 1)
    return {"games": games, "wins": wins, "losses": losses, "win_rate": wins / games}


def save_player(path, player, config, rewards):
    data = {
        "q_table": player.q_table,
        "training": asdict(config),
        "rewards": asdict(rewards),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_player(path, game, player_index):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return QLearningPlayer(game, player_index, data["q_table"])
