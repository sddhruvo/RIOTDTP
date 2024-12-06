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