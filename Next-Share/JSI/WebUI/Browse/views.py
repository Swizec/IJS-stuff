# Create your views here.

from django.http import HttpResponse

def begin(request):
    return HttpResponse("Meow")
