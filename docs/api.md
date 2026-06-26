# GeoQA Core API Documentation

GeoQA Core is written in pure, dependency-free Python. You can interact with the API directly from the QGIS Python Console, CLI scripts, or automated tests.

---

## 1. Engine API (`core/engine.py`)

### `ValidationEngine`
The central coordinator of the validation pipeline.

```python
from core.engine import ValidationEngine

# Initialize the engine
engine = ValidationEngine(profile_name="General")

# Run validation on a QGIS layer
layer_summary = engine.validate_layer(layer)

# Run validation on a list of QGIS layers (with cross-layer checks)
project_summary = engine.validate_project([layer1, layer2])
```

#### Methods:
* `__init__(self, profile_name="General")`: Instantiates the engine. Loads enabled rules for the given validation profile.
* `validate_layer(self, layer) -> LayerSummary`: Evaluates all active rules on the layer.
* `validate_project(self, layers: list) -> ProjectSummary`: Runs `validate_layer` on each layer, runs cross-layer project validations, and returns aggregated summaries.

---

## 2. Rule Base Class (`core/rules/base.py`)

### `Rule`
All framework rules inherit from this abstract base class.

```python
from core.rules import Rule
from core.models import Severity, IssueCategory

class CustomRule(Rule):
    def __init__(self):
        super().__init__(
            rule_id="C999",
            name="My Custom Check",
            description="Performs an arbitrary audit task.",
            default_severity=Severity.LOW,
            category=IssueCategory.GEOMETRY,
            recommendation="Perform the suggested resolution."
        )

    def evaluate(self, layer):
        # Implementation of evaluation logic
        # Returns a ValidationIssue if violated, otherwise None
        ...
```

#### Properties:
* `rule_id`: Unique identifier (e.g. `G001`, `A005`).
* `name`: User-visible rule title.
* `description`: What the rule checks for.
* `severity`: Current severity classification (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
* `category`: The audit domain classification (`GEOMETRY`, `CRS`, `ATTRIBUTE`, `TOPOLOGY`).
* `recommendation`: Actionable recommendation displayed to the user if the check fails.
* `enabled`: Boolean flag stating if the rule is executed.

---

## 3. Rule Loader API (`core/rules/loader.py`)

### `RuleLoader`
Scans directories and handles config loading.

```python
from core.rules.loader import RuleLoader

# Discover all rules in the directory structure
rules = RuleLoader.discover_rules()

# Load rules configured and filtered by a profile
rules = RuleLoader.load_profile_rules(profile_name="Geometry Only")
```

#### Methods:
* `discover_rules() -> List[Rule]`: Scans `core/rules/` for subclasses of `Rule`.
* `load_profile_rules(profile_name="General") -> List[Rule]`: Loads and filters discovered rules using configuration files `rules.json` and `profiles.json`.
