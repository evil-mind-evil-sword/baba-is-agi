"""Test suite for game mechanics including win/lose, movement, and interactions."""

import pytest

from baba.grid import Grid
from baba.registration import Registry


class TestWinLoseConditions:
    """Test win and lose conditions."""

    @pytest.fixture
    def game_setup(self):
        """Set up a game grid."""
        registry = Registry()
        grid = Grid(10, 10, registry)
        return grid, registry

    def test_win_condition_basic(self, game_setup):
        """Test basic win condition when YOU touches WIN."""
        grid, registry = game_setup

        # Set up BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # Set up FLAG IS WIN
        grid.place_object(registry.create_instance("flag", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("win", is_text=True), 3, 2)

        # Place objects
        baba = registry.create_instance("baba")
        flag = registry.create_instance("flag")

        grid.place_object(baba, 5, 5)
        grid.place_object(flag, 6, 5)

        grid._update_rules()

        # Initially not won
        assert not grid.won

        # Move baba onto flag
        grid.step("right")
        assert grid.won

    def test_win_with_multiple_win_objects(self, game_setup):
        """Test win condition with multiple WIN objects."""
        grid, registry = game_setup

        # Set up BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # Set up ROCK IS WIN
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("win", is_text=True), 3, 2)

        # Place objects
        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 6, 5)

        grid._update_rules()

        # Move baba onto rock
        grid.step("right")
        assert grid.won

    def test_lose_condition_no_you(self, game_setup):
        """Test lose condition when no YOU objects exist."""
        grid, registry = game_setup

        # Place text but don't form any YOU rules
        baba_text = registry.create_instance("baba", is_text=True)
        grid.place_object(baba_text, 1, 1)

        grid._update_rules()
        grid._check_win_lose()

        assert grid.lost
        assert not grid.won

    @pytest.mark.xfail(reason="Transformation removing YOU doesn't trigger lose - see workshop-83jd5lqq")
    def test_transformation_can_cause_lose(self, game_setup):
        """Test that transformations can cause a lose condition."""
        grid, registry = game_setup

        # Set up BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # Set up BABA IS ROCK (will transform BABA to ROCK)
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("rock", is_text=True), 3, 2)

        # Place baba
        baba = registry.create_instance("baba")
        grid.place_object(baba, 5, 5)

        grid._update_rules()

        # Should lose because BABA IS ROCK transforms all babas
        grid._apply_transformations()
        grid._check_win_lose()
        assert grid.lost


class TestMovementMechanics:
    """Test movement and collision mechanics."""

    @pytest.fixture
    def movement_setup(self):
        """Set up grid for movement tests."""
        registry = Registry()
        grid = Grid(10, 10, registry)

        # Always set up BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        grid._update_rules()

        return grid, registry

    def test_basic_movement(self, movement_setup):
        """Test basic movement in all directions."""
        grid, registry = movement_setup

        baba = registry.create_instance("baba")
        grid.place_object(baba, 5, 5)

        # Test movement in each direction
        grid.step("right")
        assert baba in grid.get_objects_at(6, 5)

        grid.step("down")
        assert baba in grid.get_objects_at(6, 6)

        grid.step("left")
        assert baba in grid.get_objects_at(5, 6)

        grid.step("up")
        assert baba in grid.get_objects_at(5, 5)

    def test_boundary_collision(self, movement_setup):
        """Test that objects can't move out of bounds."""
        grid, registry = movement_setup

        baba = registry.create_instance("baba")
        grid.place_object(baba, 0, 0)

        # Try to move out of bounds
        grid.step("left")
        assert baba in grid.get_objects_at(0, 0)  # Should not move

        grid.step("up")
        assert baba in grid.get_objects_at(0, 0)  # Should not move

    def test_stop_property_blocks_movement(self, movement_setup):
        """Test STOP property prevents movement."""
        grid, registry = movement_setup

        # Add WALL IS STOP
        grid.place_object(registry.create_instance("wall", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("stop", is_text=True), 3, 2)

        grid._update_rules()

        baba = registry.create_instance("baba")
        wall = registry.create_instance("wall")

        grid.place_object(baba, 5, 5)
        grid.place_object(wall, 6, 5)

        # Try to move into wall
        grid.step("right")
        assert baba in grid.get_objects_at(5, 5)  # Should not move
        assert wall in grid.get_objects_at(6, 5)  # Wall stays put

    def test_push_property_allows_pushing(self, movement_setup):
        """Test PUSH property allows objects to be pushed."""
        grid, registry = movement_setup

        # Add ROCK IS PUSH
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("push", is_text=True), 3, 2)

        grid._update_rules()

        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 6, 5)

        # Push rock
        grid.step("right")
        assert baba in grid.get_objects_at(6, 5)
        assert rock in grid.get_objects_at(7, 5)

    def test_text_is_always_pushable(self, movement_setup):
        """Test that text objects are always pushable."""
        grid, registry = movement_setup

        baba = registry.create_instance("baba")
        text_rock = registry.create_instance("rock", is_text=True)

        grid.place_object(baba, 5, 5)
        grid.place_object(text_rock, 6, 5)

        # Push text
        grid.step("right")
        assert baba in grid.get_objects_at(6, 5)
        assert text_rock in grid.get_objects_at(7, 5)

    def test_push_chain(self, movement_setup):
        """Test pushing multiple objects in a line."""
        grid, registry = movement_setup

        # Add ROCK IS PUSH
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("push", is_text=True), 3, 2)

        grid._update_rules()

        baba = registry.create_instance("baba")
        rock1 = registry.create_instance("rock")
        rock2 = registry.create_instance("rock")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock1, 6, 5)
        grid.place_object(rock2, 7, 5)

        # Push both rocks
        grid.step("right")
        assert baba in grid.get_objects_at(6, 5)
        assert rock1 in grid.get_objects_at(7, 5)
        assert rock2 in grid.get_objects_at(8, 5)

    def test_cant_push_into_wall(self, movement_setup):
        """Test can't push objects into STOP objects."""
        grid, registry = movement_setup

        # Add ROCK IS PUSH and WALL IS STOP
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("push", is_text=True), 3, 2)

        grid.place_object(registry.create_instance("wall", is_text=True), 1, 3)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 3)
        grid.place_object(registry.create_instance("stop", is_text=True), 3, 3)

        grid._update_rules()

        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")
        wall = registry.create_instance("wall")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 6, 5)
        grid.place_object(wall, 7, 5)

        # Try to push rock into wall
        grid.step("right")
        assert baba in grid.get_objects_at(5, 5)  # Can't move
        assert rock in grid.get_objects_at(6, 5)  # Rock stays
        assert wall in grid.get_objects_at(7, 5)  # Wall stays


class TestObjectTransformations:
    """Test object transformation mechanics."""

    @pytest.fixture
    def transform_setup(self):
        """Set up grid for transformation tests."""
        registry = Registry()
        grid = Grid(10, 10, registry)
        return grid, registry

    def test_simple_transformation(self, transform_setup):
        """Test NOUN IS NOUN transformation."""
        grid, registry = transform_setup

        # Set up ROCK IS BABA
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("baba", is_text=True), 3, 1)

        # Place a rock
        rock = registry.create_instance("rock")
        grid.place_object(rock, 5, 5)

        grid._update_rules()
        grid._apply_transformations()

        # Rock should be gone, baba should be there
        assert len(grid.get_objects_at(5, 5)) == 1
        transformed = list(grid.get_objects_at(5, 5))[0]
        assert transformed.name == "baba"

    def test_multiple_transformations(self, transform_setup):
        """Test multiple objects transform."""
        grid, registry = transform_setup

        # Set up ROCK IS BABA
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("baba", is_text=True), 3, 1)

        # Place multiple rocks
        positions = [(5, 5), (6, 6), (7, 7)]
        for x, y in positions:
            rock = registry.create_instance("rock")
            grid.place_object(rock, x, y)

        grid._update_rules()
        grid._apply_transformations()

        # All rocks should be babas
        for x, y in positions:
            objects = grid.get_objects_at(x, y)
            assert len(objects) == 1
            assert list(objects)[0].name == "baba"

    @pytest.mark.xfail(reason="Text objects are transformed when they shouldn't be - see workshop-8s4i3e3n")
    def test_text_not_transformed(self, transform_setup):
        """Test that text objects are not transformed."""
        grid, registry = transform_setup

        # Set up ROCK IS BABA
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("baba", is_text=True), 3, 1)

        # Place rock text
        rock_text = registry.create_instance("rock", is_text=True)
        grid.place_object(rock_text, 5, 5)

        grid._update_rules()
        grid._apply_transformations()

        # Text should not transform
        objects = grid.get_objects_at(5, 5)
        assert len(objects) == 1
        obj = list(objects)[0]
        assert obj.is_text
        assert obj.name == "rock"


class TestSinkMechanics:
    """Test SINK property mechanics."""

    @pytest.fixture
    def sink_setup(self):
        """Set up grid for sink tests."""
        registry = Registry()
        grid = Grid(10, 10, registry)

        # Set up BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # Set up WATER IS SINK
        grid.place_object(registry.create_instance("water", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("sink", is_text=True), 3, 2)

        grid._update_rules()

        return grid, registry

    def test_sink_destroys_objects(self, sink_setup):
        """Test SINK destroys objects at same position."""
        grid, registry = sink_setup

        # Place water and rock at same position
        water = registry.create_instance("water")
        rock = registry.create_instance("rock")

        grid.place_object(water, 5, 5)
        grid.place_object(rock, 5, 5)

        # Apply sink
        grid._handle_sinking()

        # Both should be destroyed
        assert len(grid.get_objects_at(5, 5)) == 0

    @pytest.mark.xfail(reason="SINK destroying YOU doesn't trigger lose - see workshop-0yf1ei9l")
    def test_moving_into_sink(self, sink_setup):
        """Test moving into SINK object destroys both."""
        grid, registry = sink_setup

        baba = registry.create_instance("baba")
        water = registry.create_instance("water")

        grid.place_object(baba, 5, 5)
        grid.place_object(water, 6, 5)

        # Move baba into water
        grid.step("right")

        # Both should be destroyed
        assert len(grid.get_objects_at(6, 5)) == 0
        assert grid.lost  # Lost because no YOU objects
