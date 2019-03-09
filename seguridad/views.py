from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse
from .forms import MyAuthForm

def index(request):
  if request.user.is_authenticated:
    return HttpResponseRedirect(reverse('pagos:index'))

  form = MyAuthForm()
  next_url = request.GET['next'] if request.GET.get('next') else ''

  return render(request, 'seguridad/index.html', {'form': form, 'next': next_url})

def log_out(request):
  logout(request)
  return HttpResponseRedirect('/')

def log_in(request):
  if request.method == 'POST':
    form = MyAuthForm(request=request, data=request.POST)

    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')

      user = authenticate(username = request.POST['username'], password = request.POST['password'])

      if user is not None:
        if user.is_active:
          login(request, user)

          if request.GET.get('next'):
            return HttpResponseRedirect(request.GET.get('next'))
          else:
            return HttpResponseRedirect(reverse('pagos:index'))
        else:
          return HttpResponse('Tu usuario fue desactivado')
      else:
        return render(request, 'seguridad/index.html', {'form': form})
    else:
      return render(request, 'seguridad/index.html', {'form': form})
  else:
    return HttpResponseRedirect(reverse('index'))




