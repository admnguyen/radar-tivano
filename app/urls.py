from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Home
    path('', views.home, name='home'),

    # PDT
    path('pdt/', views.pdt_list, name='pdt_list'),
    path('pdt/create/', views.create_pdt_page, name='create_pdt_page'),
    path('pdt/<int:pk>/', views.pdt_detail, name='pdt_detail'),
    path('pdt/<int:pk>/edit/', views.edit_pdt_page, name='edit_pdt_page'),

    # Aircraft (Samoloty)
    path('aircraft/', views.aircraft_list, name='aircraft_list'),
    path('aircraft/create/', views.create_aircraft, name='create_aircraft'),
    path('aircraft/<int:pk>/', views.aircraft_detail, name='aircraft_detail'),
    path('aircraft/<int:pk>/edit/', views.edit_aircraft, name='edit_aircraft'),

    # Pilots (Piloci)
    path('pilots/', views.pilot_list, name='pilot_list'),
    path('pilots/create/', views.create_pilot, name='create_pilot'),
    path('pilots/<int:pk>/', views.pilot_detail, name='pilot_detail'),
    path('pilots/<int:pk>/edit/', views.edit_pilot, name='edit_pilot'),
    path('pilots/<int:pk>/change-password/', views.change_password, name='change_password'),
]