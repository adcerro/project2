from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Max

from .models import User, Category,Auction, Bid

def index(request):
    data = {}
    for entry in Bid.objects.values('auction').annotate(maxbid=Max('ammount')):
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

def auction(request,id):
    try:
        auction = Auction.objects.get(pk=id)
        topbid = Bid.objects.filter(auction=auction).order_by("-ammount")[0].ammount
        if not topbid or topbid<auction.initialBid:
            bid = auction.initialBid
        else:
            bid = topbid
        if request.user.is_anonymous:
            return render(request,"auctions/auction.html",{"auction": auction,"bid": bid,"logged" : False})
        
        return render(request,"auctions/auction.html",{
        "auction": auction,
        "bid": bid,
        "logged" : True,
        "watchlist": auction in request.user.watchlist.all()
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
