from django.utils import timezone


def year(request):
    """Add a variable with current year"""
    return {
        'year': timezone.now().year,
    }
