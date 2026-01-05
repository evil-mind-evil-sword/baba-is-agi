"""
Pre-configured game environments for Baba Is You.

This module provides a collection of ready-to-play levels ranging from
simple tutorials to complex puzzles. Each environment demonstrates
different game mechanics and rule interactions.

Environments are designed to teach and challenge players with:
- Basic movement and win conditions
- Push mechanics and obstacle navigation
- Object transformations
- Complex rule manipulation
- Advanced properties like SINK, HOT/MELT, etc.
"""

import numpy as np

from .grid import Grid
from .registration import Registry


class Environment:
    """
    Base class for Baba Is You environments.

    Each environment represents a puzzle level with:
    - Fixed dimensions
    - Initial object placement
    - Starting rules (formed by text objects)
    - Difficulty rating (1-5)

    Subclasses implement setup() to create specific puzzles.
    """

    # Difficulty rating (1-5): 1=trivial, 2=easy, 3=medium, 4=hard, 5=expert
    # Subclasses should override this
    difficulty: int = 1

    def __init__(self, width: int, height: int, name: str = "Custom"):
        """
        Initialize the environment.

        Creates the grid and registry, then calls setup() to populate
        the level with objects and rules.

        Args:
            width: Width of the grid in cells
            height: Height of the grid in cells
            name: Display name for this environment
        """
        self.width = width
        self.height = height
        self.name = name
        self.registry = Registry()
        self.grid = Grid(width, height, self.registry)

        # Set up the initial state
        self.setup()

        # Update rules after setup
        # This is crucial - rules must be extracted after all text is placed
        self.grid._update_rules()

    def setup(self):
        """
        Set up the initial state of the environment.

        Override this in subclasses to:
        1. Place game objects (baba, rocks, walls, etc.)
        2. Place text objects to form rules
        3. Create the puzzle layout

        Called automatically during __init__ and reset().
        """
        pass

    def reset(self) -> Grid:
        """
        Reset the environment to its initial state.

        Creates a fresh grid and calls setup() again.
        Used when restarting a level after winning/losing.

        Returns:
            The newly created grid (observation)
        """
        self.grid = Grid(self.width, self.height, self.registry)
        self.setup()

        # Update rules after setup
        self.grid._update_rules()

        return self.grid

    def step(self, action: str) -> tuple[Grid, float, bool, dict]:
        """
        Take a step in the environment (Gym-like API).

        Args:
            action: One of ["up", "down", "left", "right", "wait"]

        Returns:
            observation: Grid object with new state
            reward: 1.0 if won, -1.0 if lost, 0.0 otherwise
            done: True if episode is over (won or lost)
            info: Dictionary with additional information
        """
        # Take the action
        won, lost = self.grid.step(action)

        # Compute reward
        reward = 0.0
        if won:
            reward = 1.0
        elif lost:
            reward = -1.0

        # Episode is done if won or lost
        done = won or lost

        # Additional info
        info = {
            "won": won,
            "lost": lost,
            "steps": self.grid.steps,
            "rules": [str(rule) for rule in self.grid.rule_manager.rules],
        }

        return self.grid, reward, done, info

    def render(self, mode: str = "rgb_array", cell_size: int = 24) -> np.ndarray:  # noqa: ARG002
        """
        Render the current state.

        Args:
            mode: Rendering mode ("rgb_array" returns numpy array)
            cell_size: Size of each cell in pixels

        Returns:
            RGB image as numpy array
        """
        return self.grid.render(cell_size)

    def get_state(self):
        """Get the current state."""
        return self.grid.get_state()

    def to_dict(self) -> dict:
        """
        Get JSON-serializable representation of current state.

        Returns:
            Dictionary containing grid state (see Grid.to_dict())
            plus environment metadata (name, difficulty)
        """
        result = self.grid.to_dict()
        result["env"] = {
            "name": self.name,
            "difficulty": self.difficulty,
        }
        return result


# Basic Environments


class SimpleEnvironment(Environment):
    """
    Simple test environment with basic rules.

    The most basic level - teaches movement and win condition.
    Layout: Baba on left, flag on right, with rules at top.
    Goal: Move Baba to the flag.
    """

    difficulty = 1  # Trivial: just walk to the flag

    def __init__(self):
        super().__init__(10, 10, "Simple")

    def setup(self):
        """
        Set up a simple level.

        Creates:
        - BABA IS YOU (player control)
        - FLAG IS WIN (objective)
        """
        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 5)

        # Place flag
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 8, 5)

        # Create rules: BABA IS YOU
        # Text objects form rules when aligned horizontally/vertically
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # Create rules: FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 6, 1)
        self.grid.place_object(is_text2, 7, 1)
        self.grid.place_object(win_text, 8, 1)


class WallMazeEnvironment(Environment):
    """Environment with walls forming a maze."""

    difficulty = 2  # Easy: navigate around walls

    def __init__(self):
        super().__init__(12, 12, "Wall Maze")

    def setup(self):
        """Set up a maze level."""
        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 1, 1)

        # Place flag
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 10, 10)

        # Create walls for maze
        wall_positions = [
            # Outer walls
            *[(x, 0) for x in range(12)],
            *[(x, 11) for x in range(12)],
            *[(0, y) for y in range(1, 11)],
            *[(11, y) for y in range(1, 11)],
            # Inner maze walls
            *[(x, 3) for x in range(1, 9)],
            *[(9, y) for y in range(1, 9)],
            *[(x, 7) for x in range(3, 11)],
            (3, 5),
            (3, 6),
            (3, 8),
            (3, 9),
            (5, 5),
            (6, 5),
            (7, 5),
        ]

        for x, y in wall_positions:
            wall = self.registry.create_instance("wall")
            self.grid.place_object(wall, x, y)

        # Create rules in a safe area
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 10)
        self.grid.place_object(is_text, 2, 10)
        self.grid.place_object(you_text, 3, 10)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 5, 10)
        self.grid.place_object(is_text2, 6, 10)
        self.grid.place_object(win_text, 7, 10)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 1, 2)
        self.grid.place_object(is_text3, 2, 2)
        self.grid.place_object(stop_text, 3, 2)


class PushPuzzleEnvironment(Environment):
    """Environment focused on pushing mechanics."""

    difficulty = 2  # Easy: push rocks out of the way

    def __init__(self):
        super().__init__(10, 8, "Push Puzzle")

    def setup(self):
        """Set up a pushing puzzle."""
        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 1, 4)

        # Place rocks to push
        rock_positions = [(3, 4), (5, 4), (7, 4)]
        for x, y in rock_positions:
            rock = self.registry.create_instance("rock")
            self.grid.place_object(rock, x, y)

        # Place flag
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 9, 4)

        # Create walls
        wall_positions = [
            *[(x, 2) for x in range(2, 9)],
            *[(x, 6) for x in range(2, 9)],
            (2, 3),
            (2, 5),
            (8, 3),
            (8, 5),
        ]

        for x, y in wall_positions:
            wall = self.registry.create_instance("wall")
            self.grid.place_object(wall, x, y)

        # Create rules
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 0)
        self.grid.place_object(is_text, 2, 0)
        self.grid.place_object(you_text, 3, 0)

        # ROCK IS PUSH
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        push_text = self.registry.create_instance("push", is_text=True)

        self.grid.place_object(rock_text, 5, 0)
        self.grid.place_object(is_text2, 6, 0)
        self.grid.place_object(push_text, 7, 0)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 1, 7)
        self.grid.place_object(is_text3, 2, 7)
        self.grid.place_object(win_text, 3, 7)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text4 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 5, 7)
        self.grid.place_object(is_text4, 6, 7)
        self.grid.place_object(stop_text, 7, 7)


class TransformationEnvironment(Environment):
    """Environment showcasing object transformation."""

    difficulty = 2  # Easy: understand transformation rules

    def __init__(self):
        super().__init__(10, 10, "Transformation")

    def setup(self):
        """Set up a transformation puzzle."""
        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 5)

        # Place water (obstacle)
        water_positions = [(x, 5) for x in range(4, 7)]
        for x, y in water_positions:
            water = self.registry.create_instance("water")
            self.grid.place_object(water, x, y)

        # Place flag
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 8, 5)

        # Place rocks (for transformation)
        rock_positions = [(2, 3), (2, 7)]
        for x, y in rock_positions:
            rock = self.registry.create_instance("rock")
            self.grid.place_object(rock, x, y)

        # Create initial rules
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 6, 1)
        self.grid.place_object(is_text2, 7, 1)
        self.grid.place_object(win_text, 8, 1)

        # WATER IS SINK
        water_text = self.registry.create_instance("water", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        sink_text = self.registry.create_instance("sink", is_text=True)

        self.grid.place_object(water_text, 1, 9)
        self.grid.place_object(is_text3, 2, 9)
        self.grid.place_object(sink_text, 3, 9)

        # ROCK IS (empty - to be filled)
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text4 = self.registry.create_instance("is", is_text=True)

        self.grid.place_object(rock_text, 6, 9)
        self.grid.place_object(is_text4, 7, 9)

        # BABA text (for transformation rule)
        baba_text2 = self.registry.create_instance("baba", is_text=True)
        self.grid.place_object(baba_text2, 8, 9)


# Extended Environments (from baba-is-ai)


class YouWinEnvironment(Environment):
    """Simple environment where agent just needs to reach the win object."""

    difficulty = 1  # Trivial: just reach the flag

    def __init__(self):
        super().__init__(6, 6, "YouWin")

    def setup(self):
        """Set up a simple you-win level."""
        # Place walls around perimeter
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place inner walls
        for x, y in [(1, 3), (1, 4), (4, 3), (4, 4)]:
            wall = self.registry.create_instance("wall")
            self.grid.place_object(wall, x, y)

        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 2)

        # Place win object (flag)
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 3, 3)

        # Create rules
        # BABA IS YOU (unbreakable)
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 1, 2)
        self.grid.place_object(is_text2, 2, 2)
        self.grid.place_object(win_text, 3, 2)


class MakeWinEnvironment(Environment):
    """Environment where agent needs to create a win rule before winning."""

    difficulty = 3  # Medium: push text to create WIN rule

    def __init__(self):
        super().__init__(8, 8, "MakeWin")

    def setup(self):
        """Set up a make-win level."""
        # Place walls around perimeter
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 2)

        # Place rock (target for win rule)
        rock = self.registry.create_instance("rock")
        self.grid.place_object(rock, 5, 5)

        # Create rules
        # BABA IS YOU (fixed position)
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # Broken ROCK IS WIN rule
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        # Place them separated so player needs to push them together
        self.grid.place_object(rock_text, 2, 4)
        self.grid.place_object(is_text2, 4, 3)
        self.grid.place_object(win_text, 6, 4)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 5, 1)
        self.grid.place_object(is_text3, 6, 1)
        self.grid.place_object(stop_text, 7, 1)


class TwoRoomEnvironment(Environment):
    """Two-room environment with a dividing wall."""

    difficulty = 2  # Easy: navigate through door

    def __init__(self):
        super().__init__(13, 9, "TwoRoom")

    def setup(self):
        """Set up a two-room level."""
        # Place walls around perimeter
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place dividing wall
        for y in range(1, self.height - 1):
            if y != 4:  # Leave a gap
                wall = self.registry.create_instance("wall")
                self.grid.place_object(wall, 6, y)

        # Place Baba in left room
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 4)

        # Place flag in right room
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 10, 4)

        # Create rules in left room
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 7, 1)
        self.grid.place_object(is_text2, 8, 1)
        self.grid.place_object(win_text, 9, 1)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 1, 7)
        self.grid.place_object(is_text3, 2, 7)
        self.grid.place_object(stop_text, 3, 7)


class TwoRoomBreakStopEnvironment(Environment):
    """Two-room environment where you need to break WALL IS STOP to pass through."""

    difficulty = 3  # Medium: break WALL IS STOP rule

    def __init__(self):
        super().__init__(13, 9, "TwoRoomBreakStop")

    def setup(self):
        """Set up a two-room level requiring breaking WALL IS STOP."""
        # Place walls around perimeter
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place complete dividing wall (no gap)
        for y in range(1, self.height - 1):
            wall = self.registry.create_instance("wall")
            self.grid.place_object(wall, 6, y)

        # Place Baba in left room
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 4)

        # Place flag in right room
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 10, 4)

        # Create rules
        # BABA IS YOU (fixed)
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # FLAG IS WIN (in right room)
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 7, 1)
        self.grid.place_object(is_text2, 8, 1)
        self.grid.place_object(win_text, 9, 1)

        # WALL IS STOP (breakable - in left room)
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 2, 6)
        self.grid.place_object(is_text3, 3, 6)
        self.grid.place_object(stop_text, 4, 6)


class MakeWinWithDistractorsEnvironment(Environment):
    """Make win environment with distractor objects and rules."""

    difficulty = 3  # Medium: distractors add complexity

    def __init__(self):
        super().__init__(10, 10, "MakeWinDistr")

    def setup(self):
        """Set up a make-win level with distractors."""
        # Place walls around perimeter
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 2)

        # Place target object (rock)
        rock = self.registry.create_instance("rock")
        self.grid.place_object(rock, 7, 7)

        # Place distractor objects
        water = self.registry.create_instance("water")
        self.grid.place_object(water, 4, 4)

        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 5, 6)

        # Create rules
        # BABA IS YOU (fixed)
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # Broken ROCK IS WIN rule
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(rock_text, 2, 5)
        self.grid.place_object(is_text2, 5, 3)
        self.grid.place_object(win_text, 8, 5)

        # Distractor rule pieces
        water_text = self.registry.create_instance("water", is_text=True)
        sink_text = self.registry.create_instance("sink", is_text=True)
        push_text = self.registry.create_instance("push", is_text=True)

        self.grid.place_object(water_text, 7, 2)
        self.grid.place_object(sink_text, 8, 3)
        self.grid.place_object(push_text, 6, 8)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 6, 1)
        self.grid.place_object(is_text3, 7, 1)
        self.grid.place_object(stop_text, 8, 1)


class GotoWinWithColorEnvironment(Environment):
    """Environment with colored objects where specific color wins."""

    difficulty = 2  # Easy: identify correct win target

    def __init__(self):
        super().__init__(8, 8, "GotoWinColor")

    def setup(self):
        """Set up a level with colored objects."""
        # Place walls around perimeter
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 4)

        # Place multiple rocks with different "colors" (positions)
        rock1 = self.registry.create_instance("rock")
        rock1.color = (255, 0, 0)  # Red
        self.grid.place_object(rock1, 4, 2)

        rock2 = self.registry.create_instance("rock")
        rock2.color = (0, 255, 0)  # Green
        self.grid.place_object(rock2, 5, 4)

        rock3 = self.registry.create_instance("rock")
        rock3.color = (0, 0, 255)  # Blue
        self.grid.place_object(rock3, 4, 6)

        # Create rules
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # ROCK IS WIN (all rocks win for simplicity)
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(rock_text, 1, 2)
        self.grid.place_object(is_text2, 2, 2)
        self.grid.place_object(win_text, 3, 2)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 5, 1)
        self.grid.place_object(is_text3, 6, 1)
        self.grid.place_object(stop_text, 7, 1)


# Advanced Environments


class MakeYouEnvironment(Environment):
    """Environment where you need to create a new YOU rule."""

    difficulty = 4  # Hard: create new YOU rule

    def __init__(self):
        super().__init__(10, 10, "MakeYou")

    def setup(self):
        """Set up a level where you need to make something else YOU."""
        # Place walls
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place horizontal wall barrier
        for x in range(1, self.width - 1):
            if x != 5:  # Leave gap
                wall = self.registry.create_instance("wall")
                self.grid.place_object(wall, x, 5)

        # Place Baba below barrier
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 5, 7)

        # Place rock above barrier
        rock = self.registry.create_instance("rock")
        self.grid.place_object(rock, 5, 3)

        # Place flag above barrier
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 7, 2)

        # BABA IS YOU (can be broken)
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 2, 7)
        self.grid.place_object(is_text, 3, 7)
        self.grid.place_object(you_text, 4, 7)

        # ROCK IS (incomplete - need to add YOU)
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)

        self.grid.place_object(rock_text, 6, 7)
        self.grid.place_object(is_text2, 7, 7)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 2, 2)
        self.grid.place_object(is_text3, 3, 2)
        self.grid.place_object(win_text, 4, 2)

        # WALL IS STOP
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text4 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 1, 1)
        self.grid.place_object(is_text4, 2, 1)
        self.grid.place_object(stop_text, 3, 1)


class TransformPuzzleEnvironment(Environment):
    """Environment where you need to transform objects to win."""

    difficulty = 3  # Medium: use transformations strategically

    def __init__(self):
        super().__init__(10, 10, "TransformPuzzle")

    def setup(self):
        """Set up a transformation puzzle."""
        # Place walls
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place water barrier
        for x in range(3, 7):
            water = self.registry.create_instance("water")
            self.grid.place_object(water, x, 5)

        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 7)

        # Place rocks (to transform)
        rock1 = self.registry.create_instance("rock")
        self.grid.place_object(rock1, 4, 7)

        rock2 = self.registry.create_instance("rock")
        self.grid.place_object(rock2, 5, 7)

        # Place flag (unreachable)
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 5, 2)

        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 5, 1)
        self.grid.place_object(is_text2, 6, 1)
        self.grid.place_object(win_text, 7, 1)

        # WATER IS SINK
        water_text = self.registry.create_instance("water", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        sink_text = self.registry.create_instance("sink", is_text=True)

        self.grid.place_object(water_text, 1, 8)
        self.grid.place_object(is_text3, 2, 8)
        self.grid.place_object(sink_text, 3, 8)

        # ROCK IS (incomplete - need BABA for transformation)
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text4 = self.registry.create_instance("is", is_text=True)

        self.grid.place_object(rock_text, 6, 8)
        self.grid.place_object(is_text4, 7, 8)

        # Extra BABA text for transformation
        baba_text2 = self.registry.create_instance("baba", is_text=True)
        self.grid.place_object(baba_text2, 8, 7)


class MultiRuleEnvironment(Environment):
    """Environment with multiple interacting rules."""

    difficulty = 4  # Hard: manage multiple rule interactions

    def __init__(self):
        super().__init__(12, 10, "MultiRule")

    def setup(self):
        """Set up a level with multiple rule interactions."""
        # Place walls
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Create compartments with walls
        for y in range(1, 9):
            wall = self.registry.create_instance("wall")
            self.grid.place_object(wall, 4, y)
            wall2 = self.registry.create_instance("wall")
            self.grid.place_object(wall2, 8, y)

        # Place objects in compartments
        # Left: Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 5)

        # Middle: Rock and Water
        rock = self.registry.create_instance("rock")
        self.grid.place_object(rock, 6, 3)

        water = self.registry.create_instance("water")
        self.grid.place_object(water, 6, 6)

        # Right: Flag
        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 10, 5)

        # Rules in left compartment
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 2)
        self.grid.place_object(is_text, 2, 2)
        self.grid.place_object(you_text, 3, 2)

        # Rules in middle compartment
        # ROCK IS PUSH
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        push_text = self.registry.create_instance("push", is_text=True)

        self.grid.place_object(rock_text, 5, 2)
        self.grid.place_object(is_text2, 6, 2)
        self.grid.place_object(push_text, 7, 2)

        # WATER IS (incomplete)
        water_text = self.registry.create_instance("water", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)

        self.grid.place_object(water_text, 5, 7)
        self.grid.place_object(is_text3, 6, 7)

        # Rules in right compartment
        # FLAG IS WIN
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text4 = self.registry.create_instance("is", is_text=True)
        win_text = self.registry.create_instance("win", is_text=True)

        self.grid.place_object(flag_text, 9, 2)
        self.grid.place_object(is_text4, 10, 2)
        self.grid.place_object(win_text, 11, 2)

        # Extra rule pieces scattered
        stop_text = self.registry.create_instance("stop", is_text=True)
        self.grid.place_object(stop_text, 2, 7)

        sink_text = self.registry.create_instance("sink", is_text=True)
        self.grid.place_object(sink_text, 10, 7)

        # WALL IS STOP (fixed)
        wall_text = self.registry.create_instance("wall", is_text=True)
        is_text5 = self.registry.create_instance("is", is_text=True)
        stop_text2 = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(wall_text, 1, 1)
        self.grid.place_object(is_text5, 2, 1)
        self.grid.place_object(stop_text2, 3, 1)


class RuleChainEnvironment(Environment):
    """Environment requiring a chain of rule manipulations."""

    difficulty = 4  # Hard: chain multiple rule changes

    def __init__(self):
        super().__init__(11, 9, "RuleChain")

    def setup(self):
        """Set up a level requiring sequential rule changes."""
        # Place walls
        for x in range(self.width):
            wall_top = self.registry.create_instance("wall")
            wall_bottom = self.registry.create_instance("wall")
            self.grid.place_object(wall_top, x, 0)
            self.grid.place_object(wall_bottom, x, self.height - 1)

        for y in range(1, self.height - 1):
            wall_left = self.registry.create_instance("wall")
            wall_right = self.registry.create_instance("wall")
            self.grid.place_object(wall_left, 0, y)
            self.grid.place_object(wall_right, self.width - 1, y)

        # Place Baba
        baba = self.registry.create_instance("baba")
        self.grid.place_object(baba, 2, 4)

        # Place objects in sequence
        rock = self.registry.create_instance("rock")
        self.grid.place_object(rock, 5, 4)

        water = self.registry.create_instance("water")
        self.grid.place_object(water, 7, 4)

        flag = self.registry.create_instance("flag")
        self.grid.place_object(flag, 9, 4)

        # Initial rules
        # BABA IS YOU
        baba_text = self.registry.create_instance("baba", is_text=True)
        is_text = self.registry.create_instance("is", is_text=True)
        you_text = self.registry.create_instance("you", is_text=True)

        self.grid.place_object(baba_text, 1, 1)
        self.grid.place_object(is_text, 2, 1)
        self.grid.place_object(you_text, 3, 1)

        # ROCK IS STOP
        rock_text = self.registry.create_instance("rock", is_text=True)
        is_text2 = self.registry.create_instance("is", is_text=True)
        stop_text = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(rock_text, 1, 2)
        self.grid.place_object(is_text2, 2, 2)
        self.grid.place_object(stop_text, 3, 2)

        # WATER IS STOP
        water_text = self.registry.create_instance("water", is_text=True)
        is_text3 = self.registry.create_instance("is", is_text=True)
        stop_text2 = self.registry.create_instance("stop", is_text=True)

        self.grid.place_object(water_text, 5, 1)
        self.grid.place_object(is_text3, 6, 1)
        self.grid.place_object(stop_text2, 7, 1)

        # FLAG IS (incomplete)
        flag_text = self.registry.create_instance("flag", is_text=True)
        is_text4 = self.registry.create_instance("is", is_text=True)

        self.grid.place_object(flag_text, 9, 1)
        self.grid.place_object(is_text4, 10, 1)

        # Scattered rule pieces
        push_text = self.registry.create_instance("push", is_text=True)
        self.grid.place_object(push_text, 3, 6)

        win_text = self.registry.create_instance("win", is_text=True)
        self.grid.place_object(win_text, 8, 7)

        sink_text = self.registry.create_instance("sink", is_text=True)
        self.grid.place_object(sink_text, 5, 7)

        # Extra IS
        is_text5 = self.registry.create_instance("is", is_text=True)
        self.grid.place_object(is_text5, 6, 6)


# Registry of all environments
ENVIRONMENTS = {
    # Basic environments
    "simple": SimpleEnvironment,
    "wall_maze": WallMazeEnvironment,
    "push_puzzle": PushPuzzleEnvironment,
    "transformation": TransformationEnvironment,
    # Extended environments
    "you_win": YouWinEnvironment,
    "make_win": MakeWinEnvironment,
    "two_room": TwoRoomEnvironment,
    "two_room_break_stop": TwoRoomBreakStopEnvironment,
    "make_win_distr": MakeWinWithDistractorsEnvironment,
    "goto_win_color": GotoWinWithColorEnvironment,
    # Advanced environments
    "make_you": MakeYouEnvironment,
    "transform_puzzle": TransformPuzzleEnvironment,
    "multi_rule": MultiRuleEnvironment,
    "rule_chain": RuleChainEnvironment,
}


def create_environment(name: str) -> Environment | None:
    """
    Create an environment by name.

    Args:
        name: Name of the environment

    Returns:
        Environment instance if found, None otherwise
    """
    env_class = ENVIRONMENTS.get(name.lower())
    if env_class:
        return env_class()
    return None


def list_environments() -> list[str]:
    """Get a list of available environment names."""
    return list(ENVIRONMENTS.keys())
