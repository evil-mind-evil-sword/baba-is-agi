"""Test suite for edge cases and complex game interactions."""

import pytest

from baba.grid import Grid
from baba.properties import Property
from baba.registration import Registry


class TestEdgeCases:
    """Test edge cases and complex interactions."""

    @pytest.fixture
    def edge_setup(self):
        """Set up grid for edge case tests."""
        registry = Registry()
        grid = Grid(10, 10, registry)
        return grid, registry

    def test_multiple_you_objects_movement(self, edge_setup):
        """Test when multiple different objects are YOU."""
        grid, registry = edge_setup

        # BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # ROCK IS YOU
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 2)

        # Place objects
        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 7, 7)

        grid._update_rules()

        # Move - both should move
        grid.step("right")

        assert baba in grid.get_objects_at(6, 5)
        assert rock in grid.get_objects_at(8, 7)

    def test_circular_transformation(self, edge_setup):
        """Test circular transformations (A IS B, B IS A)."""
        grid, registry = edge_setup

        # BABA IS ROCK
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("rock", is_text=True), 3, 1)

        # ROCK IS BABA
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("baba", is_text=True), 3, 2)

        # Place objects
        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 7, 7)

        grid._update_rules()

        # Apply transformations - should swap
        grid._apply_transformations()

        # Check that objects swapped types
        obj_at_5_5 = list(grid.get_objects_at(5, 5))[0]
        obj_at_7_7 = list(grid.get_objects_at(7, 7))[0]

        assert obj_at_5_5.name == "rock"
        assert obj_at_7_7.name == "baba"

    def test_self_transformation(self, edge_setup):
        """Test self-transformation (BABA IS BABA)."""
        grid, registry = edge_setup

        # BABA IS BABA
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("baba", is_text=True), 3, 1)

        baba = registry.create_instance("baba")
        grid.place_object(baba, 5, 5)

        grid._update_rules()
        grid._apply_transformations()

        # Should still be baba
        objects = grid.get_objects_at(5, 5)
        assert len(objects) == 1
        assert list(objects)[0].name == "baba"

    def test_contradictory_properties(self, edge_setup):
        """Test when object has contradictory properties."""
        grid, registry = edge_setup

        # ROCK IS PUSH
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("push", is_text=True), 3, 1)

        # ROCK IS STOP
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("stop", is_text=True), 3, 2)

        grid._update_rules()

        # Should have both properties
        assert grid.rule_manager.has_property("rock", Property.PUSH)
        assert grid.rule_manager.has_property("rock", Property.STOP)

        # Place objects to test behavior
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 4)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 4)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 4)

        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 6, 5)

        grid._update_rules()

        # Try to push - STOP should take precedence
        grid.step("right")
        assert baba in grid.get_objects_at(5, 5)  # Can't move

    def test_stacked_objects_win_condition(self, edge_setup):
        """Test win condition with stacked objects."""
        grid, registry = edge_setup

        # BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # FLAG IS WIN
        grid.place_object(registry.create_instance("flag", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("win", is_text=True), 3, 2)

        # Place objects stacked
        baba = registry.create_instance("baba")
        flag = registry.create_instance("flag")
        rock = registry.create_instance("rock")

        grid.place_object(flag, 5, 5)
        grid.place_object(rock, 5, 5)  # Rock on top of flag
        grid.place_object(baba, 4, 5)

        grid._update_rules()

        # Move baba onto the stack
        grid.step("right")

        # Should win even though rock is also there
        assert grid.won

    @pytest.mark.xfail(reason="Push + transformation interaction not implemented")
    def test_pushing_into_transformation(self, edge_setup):
        """Test pushing an object that then transforms."""
        grid, registry = edge_setup

        # BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # ROCK IS PUSH
        grid.place_object(registry.create_instance("rock", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("push", is_text=True), 3, 2)

        # Place objects
        baba = registry.create_instance("baba")
        rock = registry.create_instance("rock")

        # Place transformation rule text where rock will be pushed
        grid.place_object(registry.create_instance("rock", is_text=True), 7, 5)
        grid.place_object(registry.create_instance("is", is_text=True), 8, 5)
        grid.place_object(registry.create_instance("water", is_text=True), 9, 5)

        grid.place_object(baba, 5, 5)
        grid.place_object(rock, 6, 5)

        grid._update_rules()

        # Push rock onto the text
        grid.step("right")

        # Rock should have moved and then transformed
        objects_at_7_5 = grid.get_objects_at(7, 5)
        # Should have rock text and transformed water
        assert len(objects_at_7_5) == 2
        water_objects = [obj for obj in objects_at_7_5 if obj.name == "water" and not obj.is_text]
        assert len(water_objects) == 1

    @pytest.mark.xfail(reason="Breaking BABA IS YOU doesn't trigger lose - see workshop-83jd5lqq")
    def test_rule_breaking_movement(self, edge_setup):
        """Test movement that breaks its own rule."""
        grid, registry = edge_setup

        # Create BABA IS YOU using pushable text
        baba_text = registry.create_instance("baba", is_text=True)
        is_text = registry.create_instance("is", is_text=True)
        you_text = registry.create_instance("you", is_text=True)

        grid.place_object(baba_text, 4, 5)
        grid.place_object(is_text, 5, 5)
        grid.place_object(you_text, 6, 5)

        # Place baba to the left
        baba = registry.create_instance("baba")
        grid.place_object(baba, 3, 5)

        grid._update_rules()

        # Push the BABA text, breaking BABA IS YOU
        grid.step("right")

        # Baba should have moved and pushed text
        assert baba in grid.get_objects_at(4, 5)
        assert baba_text in grid.get_objects_at(5, 5)

        # After update, should lose (no YOU)
        assert grid.lost

    def test_simultaneous_win_and_sink(self, edge_setup):
        """Test what happens when WIN and SINK objects overlap."""
        grid, registry = edge_setup

        # BABA IS YOU
        grid.place_object(registry.create_instance("baba", is_text=True), 1, 1)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 1)
        grid.place_object(registry.create_instance("you", is_text=True), 3, 1)

        # FLAG IS WIN
        grid.place_object(registry.create_instance("flag", is_text=True), 1, 2)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 2)
        grid.place_object(registry.create_instance("win", is_text=True), 3, 2)

        # WATER IS SINK
        grid.place_object(registry.create_instance("water", is_text=True), 1, 3)
        grid.place_object(registry.create_instance("is", is_text=True), 2, 3)
        grid.place_object(registry.create_instance("sink", is_text=True), 3, 3)

        # Place objects
        baba = registry.create_instance("baba")
        flag = registry.create_instance("flag")
        water = registry.create_instance("water")

        grid.place_object(baba, 5, 5)
        grid.place_object(flag, 6, 5)
        grid.place_object(water, 6, 5)  # Water on flag

        grid._update_rules()

        # Move baba to flag/water position
        grid.step("right")

        # Check win is evaluated before sink
        assert grid.won

    @pytest.mark.xfail(reason="move_object returns True for non-existent objects")
    def test_empty_cell_operations(self, edge_setup):
        """Test operations on empty cells."""
        grid, registry = edge_setup

        # Try to remove from empty cell
        obj = registry.create_instance("baba")
        grid.remove_object(obj, 5, 5)  # Should not crash

        # Get objects from empty cell
        objects = grid.get_objects_at(5, 5)
        assert len(objects) == 0

        # Move from empty cell
        success = grid.move_object(obj, 5, 5, 6, 5)
        assert not success  # Can't move non-existent object
