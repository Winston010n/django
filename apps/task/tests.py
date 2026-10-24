from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from .models import Task


class SimpleTaskCachingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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
