from django.core.management.base import BaseCommand
from network_monitor.utils import get_bridge_status, manage_bridge
from network_monitor.models import NetworkInterface

class Command(BaseCommand):
    help = 'Control network bridge'

    def add_arguments(self, parser):
        parser.add_argument('action', type=str, choices=['create', 'delete', 'status'])
        parser.add_argument('--interfaces', nargs='+', type=str, help='Network interfaces to bridge')

    def handle(self, *args, **options):
        action = options['action']
        interfaces = options['interfaces']

        if action in ['create', 'delete'] and not interfaces:
            self.stderr.write('Interfaces are required for create/delete actions')
            return

        if action == 'status':
            status = get_bridge_status()
            self.stdout.write(f"Bridge Status: {'Active' if status['active'] else 'Inactive'}")
            self.stdout.write(f"Connected Interfaces: {', '.join(status['interfaces'])}")
            return

        success = manage_bridge(action, interfaces=interfaces)
        if success:
            self.stdout.write(f"Successfully {action}d bridge")
        else:
            self.stderr.write(f"Failed to {action} bridge")

# network_monitor/management/commands/snort_monitor.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from network_monitor.utils import monitor_snort_alerts
import time

class Command(BaseCommand):
    help = 'Monitor Snort alerts'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=10, 
                          help='Monitoring interval in seconds')
        parser.add_argument('--alert-file', type=str, 
                          default='/var/log/snort/alert',
                          help='Path to Snort alert file')

    def handle(self, *args, **options):
        interval = options['interval']
        alert_file = options['alert_file']
        
        self.stdout.write('Starting Snort alert monitor...')
        
        try:
            while True:
                monitor_snort_alerts(alert_file)
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write('Stopping Snort alert monitor...')

# network_monitor/management/commands/manage_rules.py
from django.core.management.base import BaseCommand
from network_monitor.utils import SnortRuleManager
from network_monitor.models import SnortRule

class Command(BaseCommand):
    help = 'Manage Snort rules'

    def add_arguments(self, parser):
        parser.add_argument('action', type=str, choices=['add', 'delete', 'list'])
        parser.add_argument('--rule-content', type=str, help='Rule content for add action')
        parser.add_argument('--rule-id', type=int, help='Rule ID for delete action')

    def handle(self, *args, **options):
        action = options['action']
        rule_manager = SnortRuleManager()

        if action == 'list':
            rules = SnortRule.objects.all()
            for rule in rules:
                self.stdout.write(f"ID: {rule.id} - {rule.rule_content}")
            return

        if action == 'add':
            content = options['rule_content']
            if not content:
                self.stderr.write('Rule content is required for add action')
                return
            
            success = rule_manager.add_rule(content)
            if success:
                SnortRule.objects.create(rule_content=content)
                self.stdout.write('Rule added successfully')
            else:
                self.stderr.write('Failed to add rule')

        if action == 'delete':
            rule_id = options['rule_id']
            if not rule_id:
                self.stderr.write('Rule ID is required for delete action')
                return
            
            try:
                rule = SnortRule.objects.get(id=rule_id)
                success = rule_manager.remove_rule(rule.rule_content)
                if success:
                    rule.delete()
                    self.stdout.write('Rule deleted successfully')
                else:
                    self.stderr.write('Failed to delete rule')
            except SnortRule.DoesNotExist:
                self.stderr.write('Rule not found')