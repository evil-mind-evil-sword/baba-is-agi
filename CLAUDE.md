# Claude Code Context for Baba Is AGI

This document provides essential context for Claude Code when working on this repository.

## Documentation

- [Level Format](docs/level_format_analysis.md) - Baba Is You file format details
- [Level Loader](docs/level_loader_documentation.md) - How to load official levels
- [Object Reference](docs/object_reference.md) - Complete list of all 120+ objects
- [Agent Framework](docs/claude_code_agent_design.md) - How to create custom AI agents
- [Claude Code Agent Design](docs/claude_code_agent_design.md) - Claude agent implementation details
- [Test Suite](tests/README.md) - Running and writing tests

## Core Philosophy: LEAN AND CLEAN

This is a **research project**. Keep the codebase minimal and focused:

- **NO backwards compatibility layers** - We move fast and break things
- **NO deprecation warnings** - Just change the API when needed
- **NO unnecessary abstractions** - Write simple, direct code
- **NO defensive programming** - Assume competent users
- **NO compatibility shims** - One way to do things
- **REMOVE code liberally** - If it's not actively used, delete it

When in doubt, choose simplicity over compatibility. This is research code that should be easy to understand, modify, and experiment with.

## Project Overview

Python implementation of Baba Is You designed for building AI agents. The project includes:
- Complete game engine with rule manipulation mechanics
- 14 pre-built environments of varying difficulty
- Clean Agent API with built-in episode management
- Gym-like Environment interface for easy integration
- Visual rendering with Pygame
- Managed with Pixi for consistent environments across platforms

**Key Design Principle:** The API is designed to be extremely simple for agent developers. You only implement `get_action()`, and the framework handles everything else (rendering, recording, statistics, etc.)

## Key Technical Details

### Pixi Dependency Management

This project uses **Pixi** for environment and dependency management. Pixi ensures consistent Python environments across all platforms without the need for manual virtualenv setup or path manipulation.

**Important Pixi Guidelines:**
- NEVER use `sys.path` manipulation in Python files - Pixi handles all path setup
- NEVER manually install packages with pip - add them to `pixi.toml` instead
- All scripts should have corresponding pixi tasks defined in `pixi.toml`
- Always run commands through pixi: `pixi run <task-name>`

**Initial Setup:**
```bash
pixi install               # Install dependencies
pixi run install           # Install package in editable mode
```

**Available Pixi Tasks:**
```bash
# Core functionality
pixi run play              # Play the game interactively
pixi run play --env maze   # Play a specific environment
pixi run test              # Run test suite

# Agent tasks
pixi run agent-random      # Run random agent
pixi run agent-demo        # Run demo agent (greedy pathfinding)
pixi run agent-claude      # Run Claude API agent (requires key)

# Environment and sprites
pixi run list-envs         # List all available environments
pixi run setup-sprites     # Copy official sprites from Steam
pixi run demo-sprites      # Demo sprite rendering
pixi run sprite-showcase   # Show all available sprites

# Development
pixi run example-agent     # Run example random agent
pixi run custom-level      # Demo custom level creation

# Code Quality
pixi run lint              # Check code with Ruff linter
pixi run lint-fix          # Auto-fix linting issues
pixi run format            # Format code with Ruff
pixi run format-check      # Check formatting without changes
pixi run typecheck         # Run Ty type checker
pixi run pre-commit-install # Install git pre-commit hooks
pixi run pre-commit-run    # Manually run all pre-commit hooks
```

**Adding New Dependencies:**
Edit `pixi.toml` and add to the `[dependencies]` section:
```toml
[dependencies]
new-package = ">=1.0"
```

Then run `pixi install` to update the environment.

### Project Structure
```
baba-is-agi/
├── baba/                 # Core game implementation
│   ├── grid.py           # Game grid and main logic
│   ├── world_object.py   # Game objects and text blocks
│   ├── rule.py           # Rule parsing and management
│   ├── properties.py     # Game properties (YOU, WIN, STOP, etc.)
│   ├── rendering.py      # Basic rendering utilities
│   ├── sprites.py        # Custom sprite generation
│   ├── sprite_loader.py  # Loads official sprites if available
│   ├── envs.py           # All game environments (14 total)
│   └── assets/sprites/   # Directory for official game sprites (gitignored)
├── agents/               # Agent implementations
│   ├── random_agent.py   # Simple random agent
│   ├── demo_agent.py     # Greedy pathfinding agent
│   └── claude_code_agent.py # Claude API agent
├── scripts/              # Utility scripts
└── pixi.toml            # Dependency management
```

### Sprite System

The game uses a dual sprite system:
1. **Custom sprites** (always available): ASCII-art based sprites defined in `sprites.py`
2. **Official sprites** (optional): Real game sprites from Steam installation

**Important**: Official sprites are copyrighted and should NEVER be committed to git. They are:
- Stored in `baba/assets/sprites/` (entire directory is gitignored)
- Automatically detected and used if present
- Fall back to custom sprites if not found

To set up official sprites (only for users who own the game):
```bash
pixi run setup-sprites
```

### Environment Interface (Gym-like API)

The game environments follow a Gym-like interface:
- `env.reset()` returns a Grid object (the observation)
- `env.step(action)` takes string actions ("up", "down", "left", "right", "wait")
- `env.step()` returns tuple: (observation, reward, done, info)
  - observation: Grid object with current state
  - reward: 1.0 if won, -1.0 if lost, 0.0 otherwise
  - done: True if episode is over (won or lost)
  - info: Dict with additional information (won, lost, steps, rules)
- `env.render(mode="rgb_array")` returns numpy array of the visual state

### Agent Development

**Simple Agent Interface:**
Agents only need to implement one method:
```python
from baba.agent import Agent
from baba.grid import Grid

class MyAgent(Agent):
    def get_action(self, observation: Grid) -> str:
        # Your logic here
        return "up"  # or "down", "left", "right", "wait"
```

**Built-in Agent Methods:**
- `agent.play_episode(env, render=True)` - Play one episode
- `agent.play_episodes(env, num_episodes=100)` - Play multiple episodes
- Recording, rendering, and stats are handled automatically!

**Accessing Game State:**
- Use `observation.rule_manager.get_you_objects()` to find controllable objects
- Use `observation.rule_manager.get_win_objects()` to find win objects
- Access grid cells with `observation.grid[y][x]` (returns set of Objects)
- Check properties with `observation.rule_manager.has_property(obj_name, Property.YOU)`
- Text objects have `is_text = True`

### Common Pitfalls

1. **Circular imports**: Be careful with imports between rule.py, world_object.py, and properties.py
2. **Object hashing**: Objects must be hashable to be stored in grid sets
3. **String formatting**: Avoid nested f-strings in list comprehensions
4. **Grid coordinates**: Grid uses [y][x] indexing, not [x][y]

### Testing

To test the game:
```bash
pixi run play           # Play interactively
pixi run agent-random   # Watch random agent play
pixi run agent-demo     # Watch demo agent solve simple levels
pixi run list-envs      # See all available environments
pixi run test           # Run test suite
```

### Code Quality

This project uses automated code quality tools:

**Linting & Formatting:**
- **Ruff** for Python linting and formatting (configuration in `pyproject.toml`)
- Line length: 100 characters
- Double quotes for strings
- Automatic import sorting

**Type Checking:**
- **Ty** for type checking (Astral's new Rust-based type checker)
- Note: Ty is in preview/beta, expect some rough edges

**Pre-commit Hooks:**
- Automatically run on every commit
- Checks linting, formatting, and types
- Install with: `pixi run pre-commit-install`

**Before committing:**
```bash
pixi run lint           # Check for linting issues
pixi run format         # Auto-format code
pixi run typecheck      # Check types
```

Or run all checks at once:
```bash
pixi run pre-commit-run
```