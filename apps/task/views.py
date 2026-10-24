from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse
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
        description='Публичный список задач. Результат кэшируется на 60 секунд.',
        responses={200: TaskSerializer(many=True)},
    )
    def get(self, request):
        # 1. Проверяем, есть ли данные в кэше
        tasks_data = cache.get("tasks")

        # Если данные есть в кэше — возвращаем их
        if tasks_data is not None:
            return Response(tasks_data)

        # 2. Если данных нет в кэше — берем из базы данных
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        tasks_data = serializer.data

        # 3. Сохраняем в кэш на 60 секунд
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
