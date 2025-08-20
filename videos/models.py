from django.db import models

# Create your models here.

class Video(models.Model):
    title = models.CharField(max_length=200)
    videofile = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
