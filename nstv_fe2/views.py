from django.shortcuts import render
from .models import Show


# Create your views here.
def index(request):
    shows = Show.objects.all()
    return render(request, context={'shows': shows}, template_name='index.html')
