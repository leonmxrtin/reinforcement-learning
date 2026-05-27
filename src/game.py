from enum import Enum
import random

class Action(Enum):
    STAY = (0, 1.0, 1.0)
    JUMP = (1, 0.9, 0.6)
    LONG_JUMP = (2, 0.7, 0.35)
    
    @property
    def jump_distance(self):
        return self.value[0]

    @property
    def dry_success(self):
        return self.value[1] 

    @property
    def slimy_success(self):
        return self.value[2]


class Game:
    def __init__(self, track_length, rng_seed=42):
        self.track_length = track_length
        self.goal_tile = track_length - 1
        self.rng = random.Random(rng_seed)

        self.player_positions = [0, 0]
        self.slime_positions = [False] + [self.rng.random() < 0.5 for _ in range(1, self.goal_tile)] + [False]
        self.winner = None
        self.round = 0
        self.current_player = 0
    
    def legal_actions(self, player):
        if player != self.current_player or self.winner is not None:
            return ()
        
        position = self.player_positions[player]
        
        actions = [Action.STAY]
        if position < self.goal_tile:
            actions.append(Action.JUMP)
        if position + 1 < self.goal_tile:
            actions.append(Action.LONG_JUMP)
        return tuple(actions)
    
    def success_probability(self, action, target):
        slimy = self.is_slimy(target)
        return action.slimy_success if slimy else action.dry_success

    def is_slimy(self, tile):
        return 0 < tile < self.goal_tile and self.slime_positions[tile]
    
    def apply_action(self, player, action):
        if player != self.current_player:
            raise ValueError(f"Wrong turn: Player {self.current_player + 1} must go")

        if action not in self.legal_actions(player):
            raise ValueError(f"Illegal action: {action}")
        
        start = self.player_positions[player]
        target = min(start + action.jump_distance, self.goal_tile)
        landed = self.rng.random() < self.success_probability(action, target)
        end = target if landed else 0
        
        self.player_positions[player] = end

        if end >= self.goal_tile:
            self.winner = player
        elif player == 1:
            self.flip_tiles()
        else:
            self.current_player += 1

    def flip_tiles(self):
        for tile in range(1, self.goal_tile):
            if tile not in self.player_positions and self.rng.random() < 0.5:
                self.slime_positions[tile] = not self.slime_positions[tile]
        self.round += 1
        self.current_player = 0
