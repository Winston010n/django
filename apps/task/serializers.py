from rest_framework import serializers
from django.utils import timezone

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "deadline",
            "is_completed",
            "time_remaining",
        )
        read_only_fields = ("id",)

    def get_time_remaining(self, task):
        if task.deadline is None:
            return "Дедлайн не указан"

        seconds_remaining = (task.deadline - timezone.now()).total_seconds()
        if seconds_remaining <= 0:
            return "Дедлайн просрочен"

        days = int(seconds_remaining // 86400)
        if days:
            unit = "day" if days == 1 else "days"
            return f"{days} {unit} left"

        hours = int(seconds_remaining // 3600)
        if hours:
            unit = "hour" if hours == 1 else "hours"
            return f"{hours} {unit} left"

        minutes = max(1, int(seconds_remaining // 60))
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit} left"

    # Валидация поля title
    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Минимум 3 символа в названии!")
        return value.strip()
