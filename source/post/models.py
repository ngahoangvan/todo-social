from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    image_path = models.CharField(max_length=255)
    image_title = models.CharField(max_length=255)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='user')
    comments_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    watchers_count = models.IntegerField(default=0)

    def __str__(self):
        return '{} - Post of {}'.format(str(self.title), str(self.author.username))


class Like(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='author_liked')
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='post_liked')

    def __str__(self):
        return '{} liked {}'.format(str(self.author.last_name), str(self.post.title))


class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='author_commented')
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='post_commented')

    def __str__(self):
        return 'Comment by {}'.format(str(self.author.username))
