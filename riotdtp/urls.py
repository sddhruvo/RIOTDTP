"""
URL configuration for riotdtp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('bridge/', BridgeConfigView.as_view(), name='bridge_config'),
    path('alerts/', AlertListView.as_view(), name='alerts'),
    path('rules/', RuleManagementView.as_view(), name='rules'),
    path('api/bridge/status/', bridge_status_api, name='bridge_status'),
    path('api/bridge/toggle/', toggle_bridge_api, name='toggle_bridge'),
    path('api/alerts/stats/', alert_stats_api, name='alert_stats'),
]
