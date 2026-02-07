from django.shortcuts import render

# Create your views here.
def landing_view(request):
    return render(request, 'core/landing.html')

def explore_view(request):
    return render(request, 'core/explore.html')