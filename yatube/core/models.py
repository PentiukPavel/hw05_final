from django.db import models


class CreateModel(models.Model):
    """Abstract model with instance date creation."""
    
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        abstract = True
