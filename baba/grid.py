"""Main game grid and environment implementation for Baba Is You."""

import copy

import cv2
import numpy as np

from .registration import Registry
from .rule import Property, RuleExtractor, RuleManager
from .world_object import Object


class Grid:
    """
    Main game grid that manages objects, rules, and game state.

    The Grid is the core data structure that:
    - Stores objects at each position (multiple objects can stack)
    - Manages game rules extracted from text objects
    - Handles object movement, collisions, and transformations
    - Tracks win/lose conditions
    - Renders the visual representation

    Key concepts:
    - Grid coordinates use [y][x] indexing (row, column)
    - Objects can stack at the same position
    - Rules are extracted from text objects aligned horizontally/vertically
    - Movement follows Baba Is You mechanics (push, stop, etc.)
    """

    def __init__(self, width: int, height: int, registry: Registry):
        """
        Initialize the grid.

        Args:
            width: Width of the grid
            height: Height of the grid
            registry: Object registry
        """
        self.width = width
        self.height = height
        self.registry = registry

        # Grid stores sets of objects at each position
        # Each cell is a set allowing multiple objects to stack
        # Indexed as grid[y][x] for row-major order
        self.grid: list[list[set[Object]]] = [[set() for _ in range(width)] for _ in range(height)]

        # Rule management components
        # RuleExtractor: Scans grid for text forming rules (e.g., BABA IS YOU)
        # RuleManager: Stores active rules and answers queries about properties
        self.rule_extractor = RuleExtractor(registry)
        self.rule_manager = RuleManager()

        # Game state tracking
        self.won = False  # Set when a YOU object touches a WIN object
        self.lost = False  # Set when no YOU objects exist
        self.steps = 0  # Total steps taken

        # Update rules initially
        self._update_rules()

    def place_object(self, obj: Object, x: int, y: int):
        """
        Place an object at a specific position.

        Args:
            obj: Object to place
            x, y: Grid coordinates
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x].add(obj)

    def remove_object(self, obj: Object, x: int, y: int):
        """
        Remove an object from a specific position.

        Args:
            obj: Object to remove
            x, y: Grid coordinates
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x].discard(obj)

    def get_objects_at(self, x: int, y: int) -> set[Object]:
        """
        Get all objects at a specific position.

        Args:
            x, y: Grid coordinates

        Returns:
            Set of objects at the position
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x].copy()
        return set()

    def move_object(self, obj: Object, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """
        Move an object from one position to another.

        Args:
            obj: Object to move
            from_x, from_y: Current position
            to_x, to_y: Target position

        Returns:
            True if move was successful
        """
        if not (0 <= to_x < self.width and 0 <= to_y < self.height):
            return False

        self.remove_object(obj, from_x, from_y)
        self.place_object(obj, to_x, to_y)
        return True

    def find_objects(
        self, obj_type: Object | None = None, name: str | None = None
    ) -> list[tuple[Object, int, int]]:
        """
        Find all objects of a specific type or name.

        Args:
            obj_type: Object type to find
            name: Object name to find

        Returns:
            List of (object, x, y) tuples
        """
        results = []
        for y in range(self.height):
            for x in range(self.width):
                for obj in self.grid[y][x]:
                    if (
                        obj_type
                        and obj.type_id == obj_type.type_id
                        or name
                        and obj.name.upper() == name.upper()
                        or not obj_type
                        and not name
                    ):
                        results.append((obj, x, y))
        return results

    def step(self, action: str) -> tuple[bool, bool]:
        """
        Execute one game step with the given action.

        Game step sequence:
        1. Move all YOU objects in the specified direction
        2. Re-extract rules from text (movement may have changed them)
        3. Apply transformations (e.g., ROCK IS BABA)
        4. Check win/lose conditions
        5. Handle SINK interactions (destroys overlapping objects)

        Args:
            action: One of 'up', 'down', 'left', 'right', 'wait'

        Returns:
            (won, lost) tuple indicating game state
        """
        self.steps += 1

        # Get movement direction
        dx, dy = 0, 0
        if action == "up":
            dx, dy = 0, -1
        elif action == "down":
            dx, dy = 0, 1
        elif action == "left":
            dx, dy = -1, 0
        elif action == "right":
            dx, dy = 1, 0

        # Move all YOU objects
        # Note: All objects with YOU property move simultaneously
        if dx != 0 or dy != 0:
            you_objects = self.rule_manager.get_you_objects()
            for obj_name in you_objects:
                # Find all instances of this object type
                for obj, x, y in self.find_objects(name=obj_name):
                    self._try_move(obj, x, y, x + dx, y + dy)

        # Update rules after movement
        self._update_rules()

        # Apply transformations
        self._apply_transformations()

        # Check win condition BEFORE sinking (WIN takes priority over SINK)
        self._check_win_lose()

        # If already won, skip sinking - WIN takes priority
        if not self.won:
            # Handle sinking
            self._handle_sinking()

            # Re-check lose condition after sinking
            # This ensures we detect loss when all YOU objects are destroyed by SINK
            self._check_win_lose()

        return self.won, self.lost

    def _try_move(self, obj: Object, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """
        Try to move an object, handling pushing and blocking.

        Movement rules:
        - Cannot move into STOP objects
        - PUSH objects can be pushed if there's space
        - Text objects are always pushable
        - Pushing chains: pushed objects can push other objects

        This method is recursive to handle push chains.

        Args:
            obj: Object to move
            from_x, from_y: Current position
            to_x, to_y: Target position

        Returns:
            True if move was successful
        """
        # Check bounds
        if not (0 <= to_x < self.width and 0 <= to_y < self.height):
            return False

        # Check what's at the target position
        target_objects = self.get_objects_at(to_x, to_y)

        # Check for STOP objects - these block all movement
        for target_obj in target_objects:
            if self.rule_manager.has_property(target_obj.name, Property.STOP):
                return False

        # Collect pushable objects at target position
        # Both PUSH property objects and all text are pushable
        push_objects = []
        for target_obj in target_objects:
            if self.rule_manager.has_property(target_obj.name, Property.PUSH) or target_obj.is_text:
                push_objects.append(target_obj)

        # If there are objects to push, try to push them
        if push_objects:
            # Calculate where to push objects (same direction)
            dx = to_x - from_x
            dy = to_y - from_y
            push_to_x = to_x + dx
            push_to_y = to_y + dy

            # All pushable objects must be able to move for the push to succeed
            # This creates push chains when objects push other objects
            for push_obj in push_objects:
                if not self._try_move(push_obj, to_x, to_y, push_to_x, push_to_y):
                    return False

        # Move is valid, execute it
        self.move_object(obj, from_x, from_y, to_x, to_y)
        return True

    def _update_rules(self):
        """
        Extract and update active rules from the grid.

        Rules are formed by text objects in patterns like:
        - NOUN IS PROPERTY (e.g., BABA IS YOU)
        - NOUN IS NOUN (e.g., ROCK IS BABA)

        Text must be aligned horizontally or vertically with no gaps.
        """
        rules = self.rule_extractor.extract_rules(self.grid)
        self.rule_manager.update_rules(rules)

    def _apply_transformations(self):
        """
        Apply object transformations based on active rules.

        Transformations occur when rules like "ROCK IS BABA" exist.
        All ROCK objects immediately transform into BABA objects.

        Note: Text objects never transform.
        """
        transformations = []

        # Collect all transformations
        for y in range(self.height):
            for x in range(self.width):
                for obj in list(self.grid[y][x]):  # Copy to avoid modification during iteration
                    # Text objects never transform - they form rules, not objects
                    if obj.is_text:
                        continue
                    transform_to = self.rule_manager.get_transformation(obj.name)
                    if transform_to:
                        # Find the target object type
                        target_obj = self.registry.get_object(transform_to.lower())
                        if target_obj:
                            transformations.append((obj, x, y, target_obj))

        # Apply transformations
        for obj, x, y, new_obj in transformations:
            self.remove_object(obj, x, y)
            # Create a new instance of the target object
            new_instance = copy.deepcopy(new_obj)
            self.place_object(new_instance, x, y)

    def _check_win_lose(self):
        """
        Check win/lose conditions.

        Win: Any YOU object overlaps with any WIN object
        Lose: No instances of YOU objects exist on the grid

        Note: Once won/lost flags are set, they persist until reset.
        """
        you_objects = self.rule_manager.get_you_objects()
        win_objects = self.rule_manager.get_win_objects()

        # Check if there are no object types with YOU property
        if not you_objects:
            self.lost = True
            return

        # Check if there are any actual instances of YOU objects on the grid
        # (The rule might say BABA IS YOU, but all babas could be destroyed)
        has_you_instance = False
        for you_name in you_objects:
            if list(self.find_objects(name=you_name)):
                has_you_instance = True
                break

        if not has_you_instance:
            self.lost = True
            return

        # Check if any YOU object is on a WIN object
        for you_name in you_objects:
            for you_obj, you_x, you_y in self.find_objects(name=you_name):
                # Check all objects at the same position
                for other_obj in self.get_objects_at(you_x, you_y):
                    if other_obj != you_obj and other_obj.name.upper() in win_objects:
                        self.won = True
                        return

    def _handle_sinking(self):
        """
        Handle SINK property interactions.

        SINK objects destroy everything at their position,
        including themselves. This happens after movement.
        """
        sink_objects = self.rule_manager.get_sink_objects()

        # Find all positions with SINK objects
        sink_positions = []
        for sink_name in sink_objects:
            for _, x, y in self.find_objects(name=sink_name):
                sink_positions.append((x, y))

        # Remove all objects at sink positions
        for x, y in sink_positions:
            self.grid[y][x].clear()

    def render(self, cell_size: int = 24) -> np.ndarray:
        """
        Render the grid as an image.

        Args:
            cell_size: Size of each cell in pixels

        Returns:
            Rendered image as numpy array
        """
        # Create dark background
        img = np.full(
            (self.height * cell_size, self.width * cell_size, 3), (20, 20, 20), dtype=np.uint8
        )

        # Add subtle grid lines
        grid_color = (35, 35, 35)
        for y in range(0, self.height * cell_size, cell_size):
            img[y : y + 1, :] = grid_color
        for x in range(0, self.width * cell_size, cell_size):
            img[:, x : x + 1] = grid_color

        # Render each cell
        for y in range(self.height):
            for x in range(self.width):
                objects = self.grid[y][x]
                if objects:
                    # Render the top object (text renders above regular objects)
                    # Sort by: text objects first, then by type_id for consistency
                    obj = max(objects, key=lambda o: (o.is_text, o.type_id))
                    sprite = obj.render((cell_size, cell_size))

                    # Place sprite in image
                    y_start = y * cell_size
                    x_start = x * cell_size
                    img[y_start : y_start + cell_size, x_start : x_start + cell_size] = sprite

                    # If there are multiple objects, add a small indicator
                    if len(objects) > 1:
                        # Add a small white dot in corner to indicate stacking
                        cv2.circle(
                            img, (x_start + cell_size - 4, y_start + 4), 2, (255, 255, 255), -1
                        )

        return img

    def get_state(self) -> np.ndarray:
        """
        Get the current state as a 3D array for AI agents.

        Encodes object type IDs at each position.
        Limited to max_objects_per_cell objects per position.

        Returns:
            State array of shape (height, width, max_objects_per_cell)
        """
        max_objects_per_cell = 3  # Adjust as needed
        state = np.zeros((self.height, self.width, max_objects_per_cell), dtype=np.int32)

        for y in range(self.height):
            for x in range(self.width):
                objects = list(self.grid[y][x])
                for i, obj in enumerate(objects[:max_objects_per_cell]):
                    state[y, x, i] = obj.type_id

        return state

    def reset(self):
        """Reset the grid to empty state."""
        self.grid = [[set() for _ in range(self.width)] for _ in range(self.height)]
        self.won = False
        self.lost = False
        self.steps = 0
        self._update_rules()

    def copy(self) -> "Grid":
        """Create a deep copy of the grid."""
        new_grid = Grid(self.width, self.height, self.registry)

        # Copy all objects
        for y in range(self.height):
            for x in range(self.width):
                for obj in self.grid[y][x]:
                    new_obj = copy.deepcopy(obj)
                    new_grid.place_object(new_obj, x, y)

        # Copy game state
        new_grid.won = self.won
        new_grid.lost = self.lost
        new_grid.steps = self.steps

        # Update rules in the new grid
        new_grid._update_rules()

        return new_grid

    def to_dict(self) -> dict:
        """
        Serialize the grid state to a JSON-compatible dictionary.

        This provides an agent-agnostic representation of the game state
        that can be communicated via JSON to any external agent.

        Returns:
            Dictionary containing:
            - dimensions: {width, height}
            - objects: list of {name, type_id, x, y, is_text}
            - rules: list of active rule strings
            - properties: dict mapping object names to their properties
            - state: {won, lost, steps}
        """
        objects = []
        for y in range(self.height):
            for x in range(self.width):
                for obj in self.grid[y][x]:
                    objects.append({
                        "name": obj.name,
                        "type_id": obj.type_id,
                        "x": x,
                        "y": y,
                        "is_text": obj.is_text,
                    })

        rules = [str(rule) for rule in self.rule_manager.rules]

        properties = {
            name: [prop.value for prop in props]
            for name, props in self.rule_manager.properties.items()
        }

        return {
            "dimensions": {"width": self.width, "height": self.height},
            "objects": objects,
            "rules": rules,
            "properties": properties,
            "transformations": dict(self.rule_manager.transformations),
            "state": {
                "won": self.won,
                "lost": self.lost,
                "steps": self.steps,
            },
        }
