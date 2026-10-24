from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task
from .serializers import TaskSerializer


class TaskView(APIView):
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        tags=['Задачи'],
        summary='Список задач',
        description=(
            'Публичный список задач. Результат без фильтров кэшируется на 60 секунд. '
            'Можно искать по названию и описанию и фильтровать по статусу выполнения.'
        ),
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Поиск по частичному совпадению в названии и описании.',
            ),
            OpenApiParameter(
                name='is_completed',
                type=OpenApiTypes.BOOL,
                description='Фильтр по статусу выполнения: true или false.',
            ),
        ],
        responses={200: TaskSerializer(many=True)},
    )
    def get(self, request):
        search = request.query_params.get('search', '').strip()
        is_completed = request.query_params.get('is_completed')

        if is_completed is not None:
            is_completed = is_completed.strip().lower()
            if is_completed not in {'true', 'false'}:
                return Response(
                    {'is_completed': ['Use "true" or "false".']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        tasks = Task.objects.all()
        if search:
            tasks = tasks.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        if is_completed is not None:
            tasks = tasks.filter(is_completed=(is_completed == 'true'))

        if not search and is_completed is None:
            tasks_data = cache.get("tasks")
            if tasks_data is not None:
                return Response(tasks_data)

        serializer = TaskSerializer(tasks, many=True)
        tasks_data = serializer.data

        if not search and is_completed is None:
            cache.set("tasks", tasks_data, 60)

        return Response(tasks_data)

    @extend_schema(
        tags=['Задачи'],
        summary='Создать задачу',
        description='Требуется аутентификация. Создание сбрасывает кэш списка задач.',
        request=TaskSerializer,
        responses={201: TaskSerializer},
    )
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 4. Очищаем кэш при создании новой задачи
        cache.delete("tasks")

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GroupedTaskView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Задачи'],
        summary='Сгруппировать задачи по дедлайну',
        description='Публичный запрос. Возвращает объект, где ключи — даты дедлайнов.',
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Словарь «дата: список задач».')},
    )
    def get(self, request):
        grouped_tasks = {}
        for task in Task.objects.order_by('deadline', 'id'):
            if task.deadline is None:
                date_key = "Без дедлайна"
            else:
                date_key = timezone.localtime(task.deadline).date().isoformat()
            grouped_tasks.setdefault(date_key, []).append(task)

        return Response({
            date: TaskSerializer(date_tasks, many=True).data
            for date, date_tasks in grouped_tasks.items()
        })


class TaskDetailView(APIView):
    serializer_class = TaskSerializer
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(tags=['Задачи'], summary='Получить задачу', description='Публичный просмотр одной задачи.', responses={200: TaskSerializer})
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    @extend_schema(tags=['Задачи'], summary='Полностью обновить задачу', description='Требуется аутентификация. Обновляет все редактируемые поля.', request=TaskSerializer, responses={200: TaskSerializer})
    def put(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Очищаем кэш при обновлении задачи
        cache.delete("tasks")
        return Response(serializer.data)

    @extend_schema(tags=['Задачи'], summary='Частично обновить задачу', description='Требуется аутентификация. Сбрасывает кэш задач.', request=TaskSerializer, responses={200: TaskSerializer})
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        cache.delete("tasks")
        return Response(serializer.data)

    @extend_schema(tags=['Задачи'], summary='Удалить задачу', description='Требуется аутентификация. Удаление сбрасывает кэш.')
    def delete(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task.delete()

        # Очищаем кэш при удалении задачи
        cache.delete("tasks")
        return Response({"message": "Задача удалена"}, status=status.HTTP_204_NO_CONTENT)
