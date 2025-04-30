from rest_framework.exceptions import APIException
from rest_framework import status


class RuleEngineError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal Rule Engine Error."
    default_code = "rule_engine_error"


class RuleNotFoundError(RuleEngineError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Rule was not found."
    default_code = "rule_not_found"


class InvalidRuleConditionError(RuleEngineError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Rule condition is invalid."
    default_code = "invalid_rule_condition"


class InvalidPayloadError(RuleEngineError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Evaluation payload is invalid."
    default_code = "invalid_payload"
