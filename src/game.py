from dataclasses import dataclass
from random import random

@dataclass(frozen=True)
class GameConfig:
    track_length: int = 10
    flip_probability: float = 0.5
    dry_jump_success: float = 0.90
    slimy_jump_success: float = 0.60
    dry_long_jump_success: float = 0.70
    slimy_long_jump_success: float = 0.35

    @property
    def goal_tile(self):
        return self.track_length - 1


class Game:
    def __init__(self, config, rng_seed):
        self.config = config
        self.rng = random.Random(rng_seed)

        self.player_positions = [0, 0]
        self.slime_positions = [self.rng.random() < 0.5 for _ in range(1, self.config.goal_tile)]
        self.winner = None
        self.round = 0
    
    def legal_actions(self, player):
        if self.winner is not None:
            return ()
        
        position = self.player_positions[player]
        
        actions = ["stay"]
        if position < self.config.goal_tile:
            actions.append("jump")
        if position + 1 < self.config.goal_tile:
            actions.append("long_jump")
        return tuple(actions)
    
    def success_probability(self, action, target):
        slimy = target < self.config.goal_tile and self.slime_positions[target - 1]
        if action == "stay":
            return 1.0
        if action == "jump":
            return self.config.slimy_jump_success if slimy else self.config.dry_jump_success
        if action == "long_jump":
            return self.config.slimy_long_jump_success if slimy else self.config.dry_long_jump_success
    
    def apply_action(self, player, action):
        if action not in self.legal_actions(player):
            raise ValueError(f"Illegal action: {action}")
        
        start = self.player_positions[player]

        if action != "stay":
            target = min(start + (1 if action == "jump" else 2), self.config.goal_tile)
            landed = self.rng.random() < self.success_probability(action, target)
            end, fell = (target, False) if landed else (0, True)
        
        self.player_positions[player] = end

        if end >= self.config.goal_tile:
            self.winner = player