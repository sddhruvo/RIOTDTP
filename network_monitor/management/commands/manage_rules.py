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