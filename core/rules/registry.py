# -*- coding: utf-8 -*-
"""Rule registry: stores, retrieves, and queries active Rule instances by ID."""
from typing import Dict, List, Optional
from .base import Rule


class RuleRegistry:
    """Manages all registered validation rules and their active states."""

    def __init__(self):
        self._rules: Dict[str, Rule] = {}

    def register(self, rule: Rule):
        """Registers a rule instance in the registry."""
        self._rules[rule.rule_id] = rule

    def unregister(self, rule_id: str):
        """Removes a rule from the registry."""
        if rule_id in self._rules:
            del self._rules[rule_id]

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Retrieves a rule instance by its ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[Rule]:
        """Returns a list of all registered rules, sorted by ID."""
        return sorted(self._rules.values(), key=lambda r: r.rule_id)

    def get_enabled_rules(self) -> List[Rule]:
        """Returns a list of all enabled registered rules."""
        return [r for r in self._rules.values() if r.enabled]

    def clear(self):
        """Clears all rules from the registry."""
        self._rules.clear()
