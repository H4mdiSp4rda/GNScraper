"""
URL configuration for GNS_Django_APP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import dashboard, sentiment_distribution_view, top_positive_entities_view, top_negative_entities_view

urlpatterns = [
    path('', dashboard, name='dashboard'),  
    path('sentiment-distribution/', sentiment_distribution_view, name='sentiment_distribution'),
    path('top-positive-entities/', top_positive_entities_view, name='top_positive_entities'),
    path('top-negative-entities/', top_negative_entities_view, name='top_negative_entities'),

]