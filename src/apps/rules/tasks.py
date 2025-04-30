from typing import List, Dict, Any
from celery import shared_task

from apps.core.exceptions import RuleNotFoundError
from .services import RuleService, RuleEvaluation


@shared_task
def evaluate_rules_async(rule_names: List[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    rule_service = RuleService()
    
    try:
        rule_conditions = rule_service.get_rules_by_names(rule_names)
        evaluation_result = RuleEvaluation.evaluate_rules(rule_conditions, payload)
        result = "APPROVED" if not evaluation_result['failed_rules'] else "REJECTED"
        return {
            'result': result,
            'passed_rules': evaluation_result['passed_rules'],
            'failed_rules': evaluation_result['failed_rules'],
            'status': 'success'
        }
    except RuleNotFoundError as e:
        return {
            'status': 'error',
            'error': str(e)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': f"An unexpected error occurred: {str(e)}"
        }
