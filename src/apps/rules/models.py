from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from django.db.models import QuerySet

from apps.core.models import BaseModel

User = get_user_model()


def validate_condition_json(condition):
    if not isinstance(condition, dict):
        raise ValidationError("Condition must be a JSON object")
    
    if "AND" in condition or "OR" in condition:
        if "AND" in condition and isinstance(condition["AND"], list):
            for subcondition in condition["AND"]:
                validate_condition_json(subcondition)
        elif "OR" in condition and isinstance(condition["OR"], list):
            for subcondition in condition["OR"]:
                validate_condition_json(subcondition)
        else:
            raise ValidationError("AND/OR conditions must contain a list of subconditions")
    else:
        validate_subcondition(condition)


def validate_subcondition(condition):
    required_keys = {"field", "operator", "value"}
    if not all(key in condition for key in required_keys):
        raise ValidationError(f"Simple condition must contain: {', '.join(required_keys)}")
    
    valid_operators = {"==", "!=", ">", "<", ">=", "<=", "contains"}
    if condition["operator"] not in valid_operators:
        raise ValidationError(f"Operator must be one of: {', '.join(valid_operators)}")


class RuleQuerySet(QuerySet):   
    def by_names(self, names):
        return self.filter(name__in=names, is_active=True)


class Rule(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    condition = models.JSONField(validators=[validate_condition_json])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rules')
    
    objects = RuleQuerySet.as_manager()
    
    def __str__(self):
        return self.name
