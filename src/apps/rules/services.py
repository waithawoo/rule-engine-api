import operator
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import QuerySet

from apps.core.exceptions import RuleNotFoundError
from .models import Rule
from .repositories import RuleRepository


class RuleService:
    def __init__(self):
        self.repository = RuleRepository()
    
    def all(self) -> QuerySet:
        return self.repository.all()
    
    def find(self, **filters) -> Optional[Rule]:
        return self.repository.get_by_filters(**filters)
    
    def create(self, **kwargs) -> Rule:
        return self.repository.create(**kwargs)

    def get_by_name(self, name: str) -> Optional[Rule]:
        return self.repository.get_by_filters(name=name)
    
    def get_rules_by_names(self, names: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
        rules = self.repository._get_queryset().by_names(names)
        found_names = set(rule.name for rule in rules)
        missing_names = set(names) - found_names
        
        if missing_names:
            raise RuleNotFoundError
        
        return [(rule.name, rule.condition) for rule in rules]


class RuleEvaluation:
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "contains": lambda a, b: b in a if isinstance(a, (list, str, dict)) else False
    }

    LOGIC_OPERATORS = {
        "AND": all,
        "OR": any
    }

    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        if "AND" in condition:
            return RuleEvaluation.LOGIC_OPERATORS["AND"](
                RuleEvaluation.evaluate_condition(subcondition, payload) for subcondition in condition["AND"]
            )
        
        if "OR" in condition:
            return RuleEvaluation.LOGIC_OPERATORS["OR"](
                RuleEvaluation.evaluate_condition(subcondition, payload) for subcondition in condition["OR"]
            )
        
        field = condition.get("field")
        op = condition.get("operator")
        value = condition.get("value")
        
        if not all([field, op, value is not None]):
            return False
        
        if op not in RuleEvaluation.OPERATORS:
            return False
        
        field_parts = field.split('.') # This is for nested field access with dot notation like "user.age"
        field_value_from_payload = payload
        
        for part in field_parts:
            if isinstance(field_value_from_payload, dict) and part in field_value_from_payload:
                field_value_from_payload = field_value_from_payload[part]
            else:
                return False
        
        try:
            return RuleEvaluation.OPERATORS[op](field_value_from_payload, value)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def evaluate_rules(rule_conditions: List[Dict[str, Any]], payload: Dict[str, Any]) -> Dict[str, List[str]]:
        passed_rules = []
        failed_rules = []
        
        for rule_name, condition in rule_conditions:
            if RuleEvaluation.evaluate_condition(condition, payload):
                passed_rules.append(rule_name)
            else:
                failed_rules.append(rule_name)
        
        return {
            "passed_rules": passed_rules,
            "failed_rules": failed_rules
        }
