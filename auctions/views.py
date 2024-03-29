from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Max

from .models import *

def index(request):
    data = {}
    for entry in Bid.objects.filter(auction__in=Auction.objects.filter(active=True)).values('auction').annotate(maxbid=Max('ammount')):
        data[Auction.objects.get(id=entry["auction"])]=entry["maxbid"]
    return render(request, "auctions/index.html",{
        "entries": data
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    
common = {"class": "form-control"}

class CreateAuction(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs=common),label="title")
    description = forms.CharField(widget=forms.TextInput(attrs=common),label="description")
    image = forms.URLField(widget=forms.URLInput(attrs=common),label="image uRL",required=False)
    category = forms.ModelChoiceField(Category.objects.all(),widget=forms.Select(attrs={"class": "form-select"}),required=False,label="category")
    price = forms.DecimalField(max_digits=11,decimal_places=2,widget=forms.NumberInput(attrs=common),label="starting bid")

@login_required
def add(request,id):
    if request.method == "POST":
        request.user.watchlist.add(Auction.objects.get(pk=id))
    return HttpResponseRedirect(reverse("auction",args={id}))

@login_required
def remove(request,id):
    if request.method == "POST":
        request.user.watchlist.remove(Auction.objects.get(pk=id))
    return HttpResponseRedirect(reverse("auction",args={id}))

class BidForm(forms.Form):
    ammount = forms.DecimalField(min_value=0,widget=forms.NumberInput(attrs=common|{"placeholder":"Bid"}))

class CommentForm(forms.Form):
    rating = forms.ChoiceField(widget=forms.Select(attrs={"class":"form-select"}),choices=models.IntegerChoices("stars","✨ ✨✨ ✨✨✨ ✨✨✨✨ ✨✨✨✨✨"))
    comment = forms.CharField(widget=forms.Textarea(attrs=common|{"placeholder":"Comment"}))

def auction(request,id):
    message = ""
    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            auction = Auction.objects.get(pk=id)
            topbid = Bid.objects.filter(auction=auction).order_by("-ammount")[0].ammount
            if form.cleaned_data["ammount"]>topbid and auction.active == True:
                bid = Bid(user=request.user,auction=auction,ammount=form.cleaned_data["ammount"])
                bid.save()
            elif not auction.active:
                message = "This auction is closed"
            else:
                message = "Your bid must be higher than the current top bid"
        else:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = Comment(user=request.user,auction=Auction.objects.get(pk=id),comment=form.cleaned_data["comment"],rating=form.cleaned_data["rating"])
                comment.save()
    try:
        auction = Auction.objects.get(pk=id)
        topbid = Bid.objects.filter(auction=auction).order_by("-ammount")[0]
        if not topbid.ammount or topbid.ammount<auction.initialBid:
            bid = Bid(auction=auction,ammount=auction.initialBid,user= auction.author)
        else:
            bid = topbid
        if request.user.is_anonymous:
            return render(request,"auctions/auction.html",{"auction": auction,"bid": bid,"logged" : False,"comments": Comment.objects.filter(auction=auction)})
        
        return render(request,"auctions/auction.html",{
        "auction": auction,
        "bid": bid,
        "logged" : True,
        "user":request.user,
        "watchlist": auction in request.user.watchlist.all(),
        "form": BidForm(),
        "message": message,
        "commentForm" : CommentForm(),
        "comments": Comment.objects.filter(auction=auction)
    })
    except Exception as e:
        print(e)
        return HttpResponseNotFound()

@login_required
def create(request):
    if request.method == "POST":
        form = CreateAuction(request.POST)
        if form.is_valid():
            image=form.cleaned_data["image"]
            if image == "":
                image = "https://photo-cdn2.icons8.com/kjvYiCHJIM8GF8Jh9fG0WFLr2otH4tU9PkmP31Ypbeo/rs:fit:288:192/czM6Ly9pY29uczgu/bW9vc2UtcHJvZC5l/eHRlcm5hbC9hMmE0/Mi83ZTUyYjc1MTk1/Nzc0MDA0OWI1NzMx/NmI3NDRkNGMzZi5q/cGc.webp"
            
            auction = Auction(author=request.user,
                              product=form.cleaned_data["title"],
                              description=form.cleaned_data["description"],
                              image=form.cleaned_data["image"],
                              category=form.cleaned_data["category"],
                              initialBid=form.cleaned_data["price"])
            auction.save()
            initialBid = Bid(user=request.user,auction=auction,ammount=form.cleaned_data["price"])
            initialBid.save()
            return HttpResponseRedirect(reverse("index"))
    return render(request, "auctions/create.html", {
        "form": CreateAuction()
    })

@login_required
def close(request,id):
    if request.method == "POST" and Auction.objects.get(pk=id).author == request.user:
        auction = Auction.objects.get(pk=id)
        auction.active = False
        auction.save()
    return HttpResponseRedirect(reverse("auction",args={id}))

def categories(request):
    return render(request,"auctions/categories.html",{
        "categories" : Category.objects.all()
    })

def category(request,id):
    data = {}
    for entry in Bid.objects.filter(auction__category__id=id).values('auction').annotate(maxbid=Max('ammount')):
        data[Auction.objects.get(id=entry["auction"])]=entry["maxbid"]
    return render(request,"auctions/category.html",{
        "entries": data,
        "category": Category.objects.get(id=id)
    })

@login_required
def watchlist(request):
    data = {}
    for entry in Bid.objects.filter(auction__in=request.user.watchlist.all()).values('auction').annotate(maxbid=Max('ammount')):
        data[Auction.objects.get(id=entry["auction"])]=entry["maxbid"]
    return render(request,"auctions/watchlist.html",{
        "watchlist": data
    })
