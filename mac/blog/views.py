from django.shortcuts import render
from .models import Blogpost
# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url='/shop/login/')
def index(request):
    myposts= Blogpost.objects.all()
    print(myposts)
    return render(request, 'blog/index.html',{"myposts": myposts})

@login_required(login_url='/shop/login/')
def blogpost(request, id):
    post = Blogpost.objects.filter(post_id = id)[0]
    print(post)
    return render(request, 'blog/blogpost.html',
                  {'post':post})
