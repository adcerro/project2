from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    watchlist = models.ManyToManyField("Auction", blank=True,null=True, related_name="watchlist") 

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    def __str__(self):
        return self.name

class Auction(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auctions")
    product = models.TextField()
    description = models.TextField()
    image = models.URLField(null=True)
    category = models.ForeignKey(Category,on_delete=models.SET_NULL, related_name="auctions",null=True)
    initialBid = models.DecimalField(max_digits=11, decimal_places=2)
    active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.product} - {self.initialBid}"

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="bids",null=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    ammount = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.user} - {self.ammount}"

class Comment(models.Model):
    rating = models.IntegerField(choices=models.IntegerChoices("stars","✨ ✨✨ ✨✨✨ ✨✨✨✨ ✨✨✨✨✨"))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="comments",null=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    def __str__(self):
        return f"{self.user} said: \n {self.comment}"
