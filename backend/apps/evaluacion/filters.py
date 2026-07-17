import django_filters
from .models import Evaluacion, CriterioEvaluacion, ResultadoEvaluacion, LeccionAprendida, Recomendacion


class EvaluacionFilter(django_filters.FilterSet):
    class Meta:
        model = Evaluacion
        fields = {
            'plan': ['exact'],
            'fiscal_year': ['exact', 'gte', 'lte'],
            'evaluation_type': ['exact'],
            'period': ['exact'],
            'status': ['exact'],
        }


class CriterioEvaluacionFilter(django_filters.FilterSet):
    class Meta:
        model = CriterioEvaluacion
        fields = {
            'evaluacion': ['exact'],
            'criterion': ['exact'],
            'score': ['gte', 'lte'],
        }


class ResultadoEvaluacionFilter(django_filters.FilterSet):
    class Meta:
        model = ResultadoEvaluacion
        fields = {
            'evaluacion': ['exact'],
            'poau': ['exact'],
            'unidad': ['exact'],
            'resultado_pad': ['exact'],
            'status': ['exact'],
            'score_global': ['gte', 'lte'],
        }


class LeccionAprendidaFilter(django_filters.FilterSet):
    class Meta:
        model = LeccionAprendida
        fields = {
            'evaluacion': ['exact'],
            'category': ['exact'],
            'title': ['icontains'],
        }


class RecomendacionFilter(django_filters.FilterSet):
    class Meta:
        model = Recomendacion
        fields = {
            'evaluacion': ['exact'],
            'priority': ['exact'],
            'status': ['exact'],
            'responsible_unit': ['icontains'],
            'due_date': ['exact', 'gte', 'lte'],
        }
