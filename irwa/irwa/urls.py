from django.conf.urls import url
from django.contrib import admin

from input import views

urlpatterns = [
    url(r'^$', views.get_game, name='get_game'),
    url(r'^admin/', admin.site.urls),
]
