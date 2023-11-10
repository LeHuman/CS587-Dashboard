from django.urls import path

from . import views

app_name = 'home'

urlpatterns = [
    path('login/', views.github_login, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('callback/', views.CallbackView.as_view(), name='callback'),
    path('choose_repo/', views.choose_repo, name='update_context'),
    path('', views.index, name='index'),
]
