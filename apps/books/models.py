from django.db import models


class Library(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Books(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='books',
        null=True,
        blank=True,
        verbose_name='Библиотека',
    )

    def __str__(self):
        return self.title
