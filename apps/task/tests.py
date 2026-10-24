from django.test import TestCase
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from .models import Task


class SimpleTaskCachingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(username="task-owner", password="StrongPassword123")
        self.client.force_authenticate(user=user)
        cache.clear()
        self.task = Task.objects.create(
            title="Купить хлеб",
            description="Свежий батон"
        )

    def test_caching_flow(self):
        # 1. Первый запрос: кэш пустой, данные читаются из базы
        res1 = self.client.get("/task/")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data), 1)

        # 2. Проверяем, что в кэше появились данные
        self.assertIsNotNone(cache.get("tasks"))

        # 3. Добавляем новую запись напрямую в базу
        Task.objects.create(title="Купить молоко", description="1 литр")

        # 4. Запрос через API по-прежнему возвращает 1 запись (из кэша)
        res2 = self.client.get("/task/")
        self.assertEqual(len(res2.data), 1)

        # 5. Делаем POST через API — кэш должен очиститься
        post_res = self.client.post("/task/", {"title": "Купить масло", "description": "Пачка"}, format="json")
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(cache.get("tasks"))

        # 6. Следующий GET вернет уже все 3 актуальные записи
        res3 = self.client.get("/task/")
        self.assertEqual(len(res3.data), 3)

    def test_deadline_status_grouping_and_patch_cache_invalidation(self):
        deadline = timezone.now() + timezone.timedelta(days=2, hours=1)
        task = Task.objects.create(
            title="Finish homework",
            deadline=deadline,
        )
        overdue_task = Task.objects.create(
            title="Past deadline",
            deadline=timezone.now() - timezone.timedelta(minutes=1),
        )

        task_response = self.client.get("/task/")
        task_payload = {item["id"]: item for item in task_response.data}
        self.assertEqual(task_payload[task.id]["time_remaining"], "2 days left")
        self.assertEqual(
            task_payload[overdue_task.id]["time_remaining"],
            "Дедлайн просрочен",
        )
        self.assertEqual(task_payload[self.task.id]["time_remaining"], "Дедлайн не указан")

        grouped_response = self.client.get("/task/grouped/")
        date_key = timezone.localtime(deadline).date().isoformat()
        self.assertEqual(grouped_response.status_code, status.HTTP_200_OK)
        self.assertEqual(grouped_response.data[date_key][0]["id"], task.id)

        patch_response = self.client.patch(
            f"/task/{task.id}/",
            {"is_completed": True},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(cache.get("tasks"))
        refreshed_response = self.client.get("/task/")
        refreshed_task = next(item for item in refreshed_response.data if item["id"] == task.id)
        self.assertTrue(refreshed_task["is_completed"])

    def test_task_search_and_completion_filter(self):
        completed_task = Task.objects.create(
            title="Проверить домашнее задание",
            description="Подготовить решение",
            is_completed=True,
        )
        Task.objects.create(title="Купить молоко", description="Для завтрака")

        search_response = self.client.get("/task/?search=домашнее")
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in search_response.data],
            [completed_task.id],
        )

        description_response = self.client.get("/task/?search=батон")
        self.assertEqual(
            [item["id"] for item in description_response.data],
            [self.task.id],
        )

        completed_response = self.client.get("/task/?is_completed=true")
        self.assertEqual(
            [item["id"] for item in completed_response.data],
            [completed_task.id],
        )

        pending_response = self.client.get("/task/?is_completed=false")
        self.assertEqual(
            {item["id"] for item in pending_response.data},
            {self.task.id, Task.objects.get(title="Купить молоко").id},
        )

        invalid_response = self.client.get("/task/?is_completed=yes")
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtered_task_list_does_not_use_unfiltered_cache(self):
        cache.set("tasks", [{"id": -1, "title": "stale"}], 60)

        response = self.client.get("/task/?search=хлеб")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [self.task.id])
