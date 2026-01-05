"""Test suite for pre-built environments."""

import pytest

from baba import make
from baba.properties import Property


class TestEnvironments:
    """Test all pre-built environments."""

    # All actual environments from envs.py
    ALL_ENVIRONMENTS = [
        # Basic
        "simple",
        "push_puzzle",
        "transformation",
        "wall_maze",
        # Extended
        "make_win",
        "make_win_distr",
        "two_room",
        "two_room_break_stop",
        "you_win",
        "goto_win_color",
        # Advanced
        "make_you",
        "multi_rule",
        "rule_chain",
        "transform_puzzle",
    ]

    def test_all_environments_load(self):
        """Test that all environments can be created without errors."""
        for env_name in self.ALL_ENVIRONMENTS:
            env = make(env_name)
            assert env is not None, f"Environment {env_name} returned None"
            assert env.grid is not None, f"Environment {env_name} has no grid"
            assert env.grid.width > 0
            assert env.grid.height > 0

    def test_simple_environment_setup(self):
        """Test simple environment has correct basic setup."""
        env = make("simple")
        grid = env.grid

        # Check that basic rules are present
        grid._update_rules()
        assert grid.rule_manager.has_property("baba", Property.YOU)

        # Check that controllable objects exist
        babas = grid.find_objects(name="baba")
        assert len(babas) > 0

    def test_make_win_environment_specific(self):
        """Test make_win environment allows creating win conditions."""
        env = make("make_win")
        grid = env.grid

        # Should start with BABA IS YOU but no WIN condition
        grid._update_rules()
        assert grid.rule_manager.has_property("baba", Property.YOU)
        assert len(grid.rule_manager.get_win_objects()) == 0

        # Check text objects are present for making rules
        text_objects = []
        for y in range(grid.height):
            for x in range(grid.width):
                for obj in grid.grid[y][x]:
                    if obj.is_text:
                        text_objects.append(obj)

        assert len(text_objects) > 0

    def test_environment_reset(self):
        """Test that environments can be reset."""
        env = make("simple")
        grid = env.grid

        # Make some changes
        grid.step("right")
        grid.step("down")

        # Reset
        new_grid = env.reset()

        # Should be a fresh grid
        assert new_grid != grid
        assert new_grid.steps == 0
        assert not new_grid.won
        assert not new_grid.lost

    @pytest.mark.parametrize("env_name", ALL_ENVIRONMENTS)
    def test_environment_step(self, env_name):
        """Test that each environment can execute a step."""
        env = make(env_name)
        grid = env.grid

        # Should be able to take at least one step
        result = grid.step("wait")
        assert result is not None
