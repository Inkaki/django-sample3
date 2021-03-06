
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.loader import get_template

import feedparser
from hashlib import sha256
import logging


from .mail import send_mail
from .models import Feed, Page
from .forms import UserForm

logger = logging.getLogger(__name__)

def index(request):
    pages = Page.objects.all()
    return render(request, 'index.html', {'pages': pages})

def post(request):
    if request.method != 'POST':
        return redirect("/")
    try:
        rss = feedparser.parse(request.POST.get('url'))
        print(rss)
    except Exception:
        return redirect("/")
    if rss.entries:
        try:
            feed = Feed.objects.create(
                title=rss.feed.title,
                description=rss.feed.subtitle,
                href=request.POST.get('url')
            )
            feed.save()
            return redirect(to="/")
        except Exception:
            raise HttpResponseServerError()
    return redirect(to="/")

def login_view(request):
    if request.method != 'POST':
        return redirect('/')
    user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
    if user is None:
        return redirect('/accounts/login')
    else:
        login(request, user)
        return redirect('/')

def create_user_view(request):
    form = UserForm()
    return render(request, 'create_user_view.html', {'form': form})



def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():

            token = sha256(('eqd131' + str(request.POST.get('username').encode('utf-8')) + ": " + str(request.POST.get('email').encode('utf-8'))).encode('utf-8')).hexdigest()

            email_html = get_template('email.html').render(
                {
                    'username': request.POST.get('username'),
                    'email': request.POST.get('email'),
                    'token': token
                }
            )
            user = User.objects.create_user(
                    username=request.POST.get('username'),
                    email=request.POST.get('email'),
                    password=request.POST.get('password'),
                    is_active=False
            )
            user.save()
            send_mail(request.POST.get('email'), "確認用メール", email_html)
            return redirect("/accounts/login")
       
    return redirect("/create_user_view")

def check_mail(request):
    user = User.objects.get(username=request.GET.get('username'))

    token = sha256(('eqd131' + str(user.username.encode('utf-8')) + ": " + str(user.email.encode('utf-8'))).encode('utf-8')).hexdigest()

    if token == request.GET.get('token'):
        user.is_active = True
        user.save()
        return redirect(to='/')
    else:
        return redirect(to='/?param=failed')

@login_required
def logout_view(request):
    logout(request)
    return redirect('/')
