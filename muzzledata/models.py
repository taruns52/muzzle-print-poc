from django.db import models

class Cow(models.Model):
    cow_name = models.CharField(max_length=100)
    cow_image = models.ImageField(upload_to='cow_images/')
    cow_encoding = models.BinaryField()

    def __str__(self):
        return self.cow_name

