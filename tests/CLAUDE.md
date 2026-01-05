# Claude Code Context for Baba Is AGI Tests

This document explains the test suite structure, what each test file validates, and the expected behavior being tested.

## Test Philosophy

Following the main CLAUDE.md philosophy of "LEAN AND CLEAN", tests should:
- Test actual behavior, not implementation details
- Be clear about what they're validating
- Avoid over-mocking or defensive testing
- Focus on core functionality

## Test Suite Overview

The test suite contains **98 tests** across 11 test files (6 xfailed for known engine limitations).

## Core Test Files

### 1. `test_grid.py` - Grid Operations (8 tests, all passing)

Tests the fundamental grid data structure that holds the game state.

**What it tests:**
- Grid initialization with correct dimensions
- Object placement and removal at specific positions
- Boundary checking (operations outside grid bounds)
- Multiple objects at same position (stacking)
- Object movement between positions
- Finding objects by name across the grid

**Why it matters:** The grid is the core data structure. If basic operations like placing/moving objects don't work, nothing else will.

### 2. `test_rules.py` - Rule System (12 tests, all passing)

Tests the rule parsing and management system that interprets text into game rules.

**What it tests:**
- Horizontal rule parsing (e.g., BABA IS YOU)
- Vertical rule parsing (rules can be formed vertically)
- Multiple simultaneous rules
- Noun-to-noun transformations (e.g., BABA IS ROCK)
- Broken rules aren't parsed (incomplete text sequences)
- Misaligned text doesn't form rules
- Rules with gaps don't parse
- Rule overrides (new rules replace old ones)
- RuleManager property queries

**Key behaviors:**
- Rules require exact alignment (horizontally or vertically)
- Text must be consecutive with no gaps
- Object names are stored in UPPERCASE internally
- Properties use the Property enum

### 3. `test_objects.py` - Object System (12 tests, all passing)

Tests the object registration and creation system.

**What it tests:**
- Registry initialization with all object types
- Creating regular game objects (baba, rock, wall, etc.)
- Creating text objects (with _text suffix in name)
- Creating property text objects (YOU, WIN, etc.)
- Invalid object creation returns None
- Object independence (instances are separate)
- Object equality (same type/attributes = equal)
- Required attributes on all objects

**Key behaviors:**
- Text objects have name suffix "_text" (e.g., "baba_text")
- Text objects have a `text` attribute with uppercase name
- Objects with same attributes compare as equal
- All objects must have: name, type_id, color, is_text

### 4. `test_all_objects.py` - Complete Object Set (13 tests, all passing)

Tests the full set of 120+ Baba Is You objects.

**What it tests:**
- Correct count of objects (44 regular, 66+ text)
- Object ID mappings match expected values
- Text object structure (noun/verb/property/special)
- All objects have required attributes
- Specific object properties (colors, IDs)
- Unique type IDs (no duplicates)
- Object categories are complete
- Property text objects (YOU, WIN, etc.)
- Verb text objects (IS, HAS, MAKE)
- Object equality and representation
- Render method exists on all objects

**Why it matters:** Validates that we've implemented the complete Baba Is You object set correctly.

### 5. `test_game_mechanics.py` - Game Logic (15 tests, 3 failing)

Tests core game mechanics like movement, collisions, and win conditions.

**What it tests:**
- **Win/Lose Conditions**
  - Basic win: YOU object touching WIN object
  - Multiple WIN objects
  - Lose when no YOU objects exist
  - Transformations causing lose (failing test)

- **Movement Mechanics**
  - Basic movement in all directions
  - Boundary collision (can't move off grid)
  - STOP property blocks movement
  - PUSH property allows pushing
  - Text is always pushable
  - Push chains (pushing multiple objects)
  - Can't push into STOP objects

- **Object Transformations**
  - Simple transformation (ROCK IS BABA)
  - Multiple objects transform
  - Text objects don't transform (failing test)

- **Sink Mechanics**
  - SINK destroys objects at same position
  - Moving into SINK destroys both (failing test)

**Expected behaviors:**
- YOU on WIN = victory
- No YOU = defeat
- STOP blocks all movement
- PUSH objects can be moved by YOU objects
- Text is always pushable regardless of rules
- Transformations change object type
- SINK destroys everything at that position

### 6. `test_edge_cases.py` - Complex Interactions (9 tests, 3 failing)

Tests complex scenarios and edge cases.

**What it tests:**
- Multiple YOU objects move together
- Circular transformations (A IS B, B IS A)
- Self-transformation (BABA IS BABA)
- Contradictory properties (PUSH and STOP)
- Stacked objects and win conditions
- Pushing into transformation zones (failing)
- Rule-breaking movement (failing)
- Simultaneous WIN and SINK
- Empty cell operations (failing)

**Why these matter:** Real gameplay involves complex rule interactions that can break naive implementations.

### 7. `test_environments.py` - Level Loading (10 tests, 8 failing)

Tests the pre-built game environments and level loading.

**What it tests:**
- All 14 environments load without errors
- Environment-specific setups (tutorial, puzzle, etc.)
- Level loader initialization
- Environment reset functionality

**Current issues:** 
- Tests expect `load_from_dict` method that doesn't exist
- Some environments may not be properly initialized
- Integration with level loader needs work

### 8. `test_level_loader.py` - Level Loading System (7 tests, 3 failing)

Tests the level file loading system.

**What it tests:**
- Level loader initialization
- Steam level detection
- Loading basic levels from .l files
- Object ID to name mapping
- Multiple level loading

**Current issues:**
- Tests for dictionary loading don't match implementation
- Some object ID mappings may be incorrect

### 9. `test_integration.py` - Full Game Scenarios (9 tests, 4 failing)

Integration tests that play through game scenarios.

**What it tests:**
- Completing simple levels
- Tutorial level puzzle solving
- Transformation level gameplay
- Creating WIN rules dynamically
- Sink level interactions
- Multiple YOU control
- Complex rule levels
- Game state persistence
- Agent compatibility interface

**Why these fail:** Integration tests are sensitive to exact game behavior and level design.

### 10. `test_all_objects_integration.py` - Object Integration (5 tests, all passing)

Tests how the complete object set integrates with the game system.

**What it tests:**
- Creating grids with various objects
- Rules work with new object types (KEKE IS YOU)
- Level loader integration with all objects
- Object property consistency
- Rendering all object types

### 11. `test_rules.py` - Rule System (12 tests, all passing)

Covered above in #2.

## Test Patterns and Conventions

### Fixtures
Most tests use pytest fixtures for setup:
```python
@pytest.fixture
def setup(self):
    registry = Registry()
    grid = Grid(10, 10, registry)
    return grid, registry
```

### Assertions
Tests make explicit assertions about expected behavior:
```python
# Object should exist at specific position
assert baba in grid.get_objects_at(5, 5)

# Rule should be active
assert grid.rule_manager.has_property("baba", Property.YOU)

# Game should be won
assert grid.won
```

### Test Organization
- Unit tests: Test individual components (grid, rules, objects)
- Integration tests: Test complete scenarios
- Edge case tests: Test unusual interactions

## Common Test Failures and Solutions

### 1. Case Sensitivity
- Internal system uses UPPERCASE for object names in rules
- Tests must use correct case when checking rules

### 2. Object Naming
- Regular objects: "baba", "rock", "wall"
- Text objects: "baba_text", "rock_text", "wall_text"
- Text objects created with `is_text=True` parameter

### 3. Missing Methods
- Some tests expect methods that don't exist (e.g., `load_from_dict`)
- Either implement the methods or update tests to match reality

### 4. Property vs String
- Properties should use the Property enum, not strings
- Example: `Property.YOU` not `"YOU"`

## Running Tests

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run test tests/test_grid.py

# Run with verbose output
pixi run test -v

# Run specific test class
pixi run test tests/test_rules.py::TestRuleParsing

# Run with coverage
pixi run test-coverage
```

## Test Philosophy Notes

1. **Test Behavior, Not Implementation**
   - Don't test private methods
   - Test observable outcomes
   - Avoid testing exact error messages

2. **Clear Test Names**
   - Test method names should explain what they test
   - Use docstrings to provide additional context

3. **Isolated Tests**
   - Each test should be independent
   - Use fixtures for setup, not shared state
   - Clean up after tests if needed

4. **Realistic Scenarios**
   - Test cases should reflect actual game situations
   - Avoid contrived edge cases that can't happen in real gameplay

5. **Performance**
   - Keep tests fast
   - Mock expensive operations if needed
   - Use skipif for tests requiring external resources

## Future Test Improvements

1. **Visual Testing**
   - Add tests for sprite rendering
   - Validate visual output matches expected appearance

2. **Performance Tests**
   - Test grid operations with many objects
   - Benchmark rule parsing with complex rule sets

3. **Save/Load Tests**
   - Test game state serialization
   - Validate level saving and loading

4. **Agent Interface Tests**
   - Ensure the game provides correct interface for AI agents
   - Test observation and action spaces

Remember: Tests are documentation. A good test explains what the system should do and why.