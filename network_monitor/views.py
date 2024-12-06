# views.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.http import JsonResponse
from rest_framework.viewsets import ModelViewSet
from .models import NetworkInterface, BridgeConfiguration, SnortAlert, SnortRule
from .utils import manage_bridge, get_snort_stats, get_bridge_status, SnortRuleManager
from .serializers import AlertSerializer, InterfaceSerializer

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'network_monitor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'snort_stats': get_snort_stats(),
            'bridge_status': get_bridge_status(),
            'recent_alerts': SnortAlert.objects.order_by('-timestamp')[:10],
            'interfaces': NetworkInterface.objects.all()
        })
        return context

class BridgeConfigView(LoginRequiredMixin, CreateView):
    model = BridgeConfiguration
    template_name = 'network_monitor/bridge_config.html'
    fields = ['name', 'interfaces']
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        success = manage_bridge('create', 
                              interfaces=form.cleaned_data['interfaces'])
        if not success:
            form.add_error(None, "Failed to create bridge")
            return self.form_invalid(form)
        return response

class BridgeDeleteView(LoginRequiredMixin, DeleteView):
    model = BridgeConfiguration
    success_url = reverse_lazy('dashboard')

    def delete(self, request, *args, **kwargs):
        bridge = self.get_object()
        success = manage_bridge('delete', interfaces=bridge.interfaces.all())
        if success:
            return super().delete(request, *args, **kwargs)
        return JsonResponse({'error': 'Failed to delete bridge'}, status=400)

class AlertListView(LoginRequiredMixin, ListView):
    model = SnortAlert
    template_name = 'network_monitor/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {}
        
        priority = self.request.GET.get('priority')
        if priority:
            filters['priority'] = priority
            
        source_ip = self.request.GET.get('source_ip')
        if source_ip:
            filters['source_ip'] = source_ip
            
        return queryset.filter(**filters).order_by('-timestamp')

class RuleManagementView(LoginRequiredMixin, ListView):
    model = SnortRule
    template_name = 'network_monitor/rule_management.html'
    context_object_name = 'rules'

    def post(self, request):
        action = request.POST.get('action')
        rule_manager = SnortRuleManager()
        
        if action == 'add':
            content = request.POST.get('rule_content')
            success = rule_manager.add_rule(content)
            if success:
                SnortRule.objects.create(rule_content=content)
        
        elif action == 'delete':
            rule_id = request.POST.get('rule_id')
            rule = SnortRule.objects.get(id=rule_id)
            success = rule_manager.remove_rule(rule.rule_content)
            if success:
                rule.delete()
                
        return redirect('rules')

class InterfaceViewSet(ModelViewSet):
    queryset = NetworkInterface.objects.all()
    serializer_class = InterfaceSerializer

class AlertViewSet(ModelViewSet):
    queryset = SnortAlert.objects.all()
    serializer_class = AlertSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset.order_by('-timestamp')

def bridge_status_api(request):
    status = get_bridge_status()
    return JsonResponse(status)

def toggle_bridge_api(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        bridge_config = BridgeConfiguration.objects.first()
        
        if not bridge_config:
            return JsonResponse({
                'error': 'No bridge configuration found'
            }, status=400)
            
        success = manage_bridge(
            action,
            interfaces=bridge_config.interfaces.all()
        )
        
        return JsonResponse({
            'success': success,
            'status': get_bridge_status()
        })

def alert_stats_api(request):
    return JsonResponse(get_snort_stats())