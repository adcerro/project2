from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Auction(models.Model):
    product = models.TextField()
    description = models.TextField()
    image = models.URLField(null=True)
    category = models.ForeignKey(Category,on_delete=models.SET_NULL, related_name="auctions",null=True)
    price = models.DecimalField(max_digits=11, decimal_places=2)
    def __str__(self):
        return f"{self.product} - {self.price}"

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="bids",null=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    ammount = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.user} - {self.ammount}"

class Comment(models.Model):
    rating = models.IntegerChoices("stars","✨ ✨✨ ✨✨✨ ✨✨✨✨ ✨✨✨✨✨")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="comments",null=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    def __str__(self):
        return f"{self.user} \n {self.comment}"
