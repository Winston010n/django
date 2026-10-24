from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=60)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
