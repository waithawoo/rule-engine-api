from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RuleViewSet, RuleEvaluationViewSet

router = DefaultRouter()
router.register(r'rules', RuleViewSet, basename='rule')
router.register(r'rule-evaluation', RuleEvaluationViewSet, basename='rule-evaluation')

urlpatterns = [
    path('', include(router.urls)),
]
