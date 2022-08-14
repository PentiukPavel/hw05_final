from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относится пост',
        }
        error_messages = {
            'text': {
                'blank': 'Текст поста не может быть пустым.',
            }
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария'
        }
        help_texts = {
            'text': 'Текст комментария'
        }
        error_messages = {
            'text': {
                'blank': 'Текст комментария не может быть пустым.',
            }
        }
