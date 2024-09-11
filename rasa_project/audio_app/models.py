from django.db import models
from auth_app.models import CustomUser



class MyAudioFile(models.Model):
    """
    Model to store the name of the audio file and its unique hash (not the actual file).
    """
    file_name = models.CharField(max_length=255,null=True,blank=True)
    file_hash = models.CharField(max_length=100, unique=True)
    myaudio_url = models.URLField(max_length=500, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    contributor= models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.file_name} - {self.hash}"

# Create your models here.
