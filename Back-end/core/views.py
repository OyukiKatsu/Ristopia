from django.shortcuts import render


def Index(request):
    return render(request, 'core/index.html')

def error_403(request, exception=None):
    return render(request, 'core/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'core/404.html', status=404)

def error_400(request, exception=None):
    return render(request, 'core/400.html', status=400)