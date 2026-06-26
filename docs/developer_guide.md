# GeoQA Framework Developer Guide

Adding a new validation rule to the GeoQA framework is simple and does not require modifying the central execution engine. This guide walks you through implementing a new rule.

---

## Step 1: Create the Rule File

Decide which domain category your rule belongs to:
- Geometry (`core/rules/geometry/`)
- CRS (`core/rules/crs/`)
- Attributes (`core/rules/attributes/`)

Create a new Python file in the corresponding folder. Use the rule ID and name for the file name (e.g. `a007_missing_emails.py`).

---

## Step 2: Implement the Rule Subclass

Create a Python class that inherits from the base `Rule` class.

### Example:
Create `core/rules/attributes/a007_missing_emails.py`:

```python
from core.rules import Rule
from core.models import ValidationIssue, IssueCategory, Severity

class A007_MissingEmails(Rule):
    """Checks if email string fields contain a valid '@' domain symbol."""

    def __init__(self):
        super().__init__(
            rule_id="A007",
            name="Invalid Email Addresses",
            description="Scans fields with 'email' in their name for valid domain characters.",
            default_severity=Severity.LOW,
            category=IssueCategory.ATTRIBUTE,
            recommendation="Update email fields to include a valid email domain address (e.g., user@domain.com)."
        )

    def evaluate(self, layer):
        # 1. Check if layer has fields
        if not hasattr(layer, "fields"):
            return None

        # 2. Find target fields containing 'email'
        email_fields = [f.name() for f in layer.fields() if "email" in f.name().lower()]
        if not email_fields:
            return None

        invalid_fids = []

        # 3. Scan features
        for feature in layer.getFeatures():
            fid = feature.id()
            for field in email_fields:
                val = feature[field]
                if val is not None and "@" not in str(val):
                    invalid_fids.append(fid)

        # 4. Return ValidationIssue if any failures were found
        if invalid_fids:
            return ValidationIssue(
                category=self.category,
                severity=self.severity,
                message=f"Field '{email_fields[0]}' contains {len(invalid_fids)} invalid email strings.",
                recommendation=self.recommendation,
                affected_features=invalid_fids,
                field_name=email_fields[0]
            )

        return None
```

---

## Step 3: Registering the Rule

**You don't need to do anything to register the rule class!**

The `RuleLoader` automatically scans all submodules in the `core/rules/` directory recursively. When the engine starts, it will discover `A007_MissingEmails`, load it, and execute it automatically.

### Configuring defaults (Optional)
If you want to override the rule status or severity defaults globally without changing code, add it to `rules.json`:

```json
{
  "A007": {
    "enabled": true,
    "severity": "Low"
  }
}
```

And add it to domain profile presets in `profiles.json` if needed.
