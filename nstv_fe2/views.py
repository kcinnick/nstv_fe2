from django.shortcuts import render
from .models import Show


# Create your views here.
def index(request):
    shows = Show.objects.all()
    print(shows)
    return render(request, template_name='index.html')
