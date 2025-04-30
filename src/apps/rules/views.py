from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.core.exceptions import RuleNotFoundError, InvalidPayloadError
from apps.core.permissions import IsAdminUser, IsClientUser
from .models import Rule
from .serializers import (
    RuleSerializer, 
    RuleEvaluationRequestSerializer,
    RuleEvaluationResponseSerializer,
    RuleEvaluationAsyncResponseSerializer
)
from .services import RuleService, RuleEvaluation
from .tasks import evaluate_rules_async


class RuleViewSet(viewsets.ModelViewSet):
    serializer_class = RuleSerializer
    permission_classes = [IsAdminUser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rule_service = RuleService()
    
    def get_queryset(self):
        return self.rule_service.all()
    
    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        self.rule_service.create(created_by=self.request.user, **validated_data)


class RuleEvaluationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rule_service = RuleService()
    
    @swagger_auto_schema(
        request_body=RuleEvaluationRequestSerializer,
        responses={
            200: RuleEvaluationResponseSerializer,
            400: "Bad Request",
            404: "Rule Not Found",
            500: "Server Error"
        },
        operation_description="Evaluate a payload against the specified rules. Returns APPROVED if all rules pass, REJECTED if any rule fails.",
        operation_summary="Evaluate Rules"
    )
    @action(detail=False, methods=['post'])
    def evaluate(self, request):
        serializer = RuleEvaluationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        rule_names = serializer.validated_data['rules']
        payload = serializer.validated_data['payload']
        
        try:
            rule_conditions = self.rule_service.get_rules_by_names(rule_names)
            evaluation_result = RuleEvaluation.evaluate_rules(rule_conditions, payload)
            result = "APPROVED" if not evaluation_result['failed_rules'] else "REJECTED"
            
            response_data = {
                'result': result,
                'passed_rules': evaluation_result['passed_rules'],
                'failed_rules': evaluation_result['failed_rules']
            }
            
            response_serializer = RuleEvaluationResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data)
        except RuleNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=RuleEvaluationRequestSerializer,
        responses={
            200: RuleEvaluationAsyncResponseSerializer,
            400: "Bad Request",
            404: "Rule Not Found",
            500: "Server Error"
        },
        operation_description="Evaluate a payload against the specified rules. Returns task_id and task status",
        operation_summary="Evaluate Rules Async"
    )
    @action(detail=False, methods=['post'])
    def evaluate_async(self, request):
        serializer = RuleEvaluationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        rule_names = serializer.validated_data['rules']
        payload = serializer.validated_data['payload']
        
        try:
            self.rule_service.get_rules_by_names(rule_names)
        except RuleNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        task = evaluate_rules_async.delay(
            rule_names=rule_names,
            payload=payload
        )

        return Response({
            'task_id': task.id,
            'status': 'pending',
            'message': 'Rule evaluation has been scheduled'
        }, status=status.HTTP_202_ACCEPTED)
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'task_id', openapi.IN_QUERY, description="Celery task ID",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        operation_summary="Check rule evaluation task result",
        operation_description="Returns the status or result of a background task given its task_id."
    )
    @action(detail=False, methods=['get'])
    def task_result(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'detail': 'task_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task = evaluate_rules_async.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return Response({
                'task_id': task_id,
                'status': 'pending',
                'message': 'Task is still in progress'
            })
        elif task.state == 'SUCCESS':
            result = task.result
            if result.get('status') == 'error':
                return Response({
                    'task_id': task_id,
                    'status': 'error',
                    'detail': result.get('error')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            response_data = {
                'result': result.get('result'),
                'passed_rules': result.get('passed_rules'),
                'failed_rules': result.get('failed_rules')
            }
            
            response_serializer = RuleEvaluationResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data)
        else:
            return Response({
                'task_id': task_id,
                'status': 'error',
                'detail': f'Task failed with status: {task.state}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
