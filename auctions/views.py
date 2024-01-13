from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Category,Auction


def index(request):
    return render(request, "auctions/index.html")


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
def create(request):
    if request.method == "POST":
        form = CreateAuction(request.POST)
        if form.is_valid():
            print(type(form.cleaned_data["price"]))
            auction = Auction(product=form.cleaned_data["title"],
                              description=form.cleaned_data["description"],
                              image=form.cleaned_data["image"],
                              category=form.cleaned_data["category"],
                              price=round(form.cleaned_data["price"],2))
            auction.save()
    return render(request, "auctions/create.html", {
        "form": CreateAuction()
    })
