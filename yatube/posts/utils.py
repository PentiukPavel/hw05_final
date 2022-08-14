from django.core.paginator import Paginator

from yatube.settings import POST_PER_PAGE


def page_counter(request, posts: object) -> Paginator:
    """Retrieve paginator"""
    paginator = Paginator(posts, per_page=POST_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
