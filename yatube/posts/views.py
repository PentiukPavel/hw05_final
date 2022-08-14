from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import page_counter


@cache_page(20, key_prefix='index_page')
def index(request) -> HttpResponse:
    template = 'posts/index.html'
    posts = Post.objects.all().select_related('group', 'author')
    page_obj = page_counter(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug: str) -> HttpResponse:
    """Retrive posts of certain group"""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().select_related('author')
    page_obj = page_counter(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username: str) -> HttpResponse:
    """Retrive posts of certain author"""
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    posts = author.posts.all().select_related('group')
    page_obj = page_counter(request, posts)
    posts_quantity = author.posts.all().count()
    context = {
        'page_obj': page_obj,
        'posts_quantity': posts_quantity,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id: int) -> HttpResponse:
    """Retrive certain post"""
    post = get_object_or_404(Post, pk=post_id)
    comment_form = CommentForm(request.POST or None)
    comments = post.comments.all()
    post_text_preview = f'Пост {post.text[:30]}...'
    posts_quantity = post.author.posts.all().count()
    context = {
        'post_text_preview': post_text_preview,
        'post': post,
        'posts_quantity': posts_quantity,
        'post_id': post_id,
        'comments': comments,
        'form': comment_form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request) -> HttpResponse:
    """New post creation"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id: int) -> HttpResponse:
    """Post changing"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id: int) -> HttpResponse:
    """Comment creation"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request) -> HttpResponse:
    """Retrive posts of favorite authors"""
    favorite_authors = []
    for obj in request.user.follower.all():
        favorite_authors.append(obj.author)
    posts = Post.objects.filter(
        author__in=favorite_authors
    ).select_related('group', 'author')
    page_obj = page_counter(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username) -> HttpResponse:
    """Follow an author"""
    author = User.objects.get(username=username)
    if request.user == author:
        return redirect('posts:profile', username)
    favorite_authors = Follow.objects.filter(
        user=request.user,
        author=author
    )
    if favorite_authors.exists():
        return redirect('posts:profile', username)
    favorite_author = Follow.objects.create(
        user=request.user,
        author=author,
    )
    favorite_author.save()
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    subscription = Follow.objects.get(
        user=request.user,
        author=User.objects.get(username=username),
    )
    subscription.delete()
    return redirect('posts:profile', username)
