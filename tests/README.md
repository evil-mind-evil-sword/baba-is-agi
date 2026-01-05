# Baba Is AGI Tests

Comprehensive test suite with 98 test cases (6 xfailed for known engine limitations).

## Running Tests

```bash
pixi run test              # All tests
pixi run test-verbose      # Detailed output
pixi run test-coverage     # Coverage report
pixi run test-unit         # Fast unit tests
pixi run test-integration  # Slower integration tests
```

## Test Organization

### Unit Tests
- `test_grid.py` - Grid operations
- `test_rules.py` - Rule system
- `test_objects.py` - Object registry
- `test_game_mechanics.py` - Game logic

### Integration Tests  
- `test_environments.py` - Level loading
- `test_edge_cases.py` - Complex scenarios
- `test_integration.py` - Full gameplay

### Object Tests
- `test_all_objects.py` - All 120+ objects
- `test_all_objects_integration.py` - Object interactions

## Test Coverage

- Grid operations and boundaries
- Rule parsing and properties
- Win/lose conditions
- Push/stop mechanics
- Object transformations
- All 14 environments
- Edge cases (multiple YOU, circular rules)

## Writing Tests

```python
class TestFeature:
    @pytest.fixture
    def setup(self):
        registry = Registry()
        grid = Grid(10, 10, registry)
        return grid, registry
    
    def test_behavior(self, setup):
        grid, registry = setup
        # Test implementation
```

Mark categories:
```python
@pytest.mark.slow         # Long-running tests
@pytest.mark.integration  # Full scenarios
```