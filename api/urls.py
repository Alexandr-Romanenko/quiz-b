from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionnaireViewSet, QuestionViewSet, AnswerViewSet

router = DefaultRouter()
router.register(r'questionnaires', QuestionnaireViewSet, basename='questionnaires')
router.register(r'questions', QuestionViewSet, basename='questions')
router.register(r'answers', AnswerViewSet, basename='answers')
urlpatterns = router.urls
