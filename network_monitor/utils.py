import subprocess
import re
import json
import logging
import psutil
from datetime import datetime
from .models import NetworkInterface, SnortAlert, BridgeConfiguration

logger = logging.getLogger(__name__)

def get_network_interfaces():
    """Get all network interfaces except loopback"""
    interfaces = []
    for iface, addrs in psutil.net_if_addrs().items():
        if iface != 'lo':
            mac = next((addr.address for addr in addrs if addr.family == psutil.AF_LINK), None)
            ip = next((addr.address for addr in addrs if addr.family == socket.AF_INET), None)
            interfaces.append({
                'name': iface,
                'mac': mac,
                'ip': ip
            })
    return interfaces

def manage_bridge(action, bridge_name='br0', interfaces=None):
    """Manage network bridge"""
    try:
        if action == 'create':
            subprocess.run(['sudo', 'brctl', 'addbr', bridge_name], check=True)
            for iface in interfaces:
                subprocess.run(['sudo', 'ip', 'link', 'set', iface, 'down'], check=True)
                subprocess.run(['sudo', 'brctl', 'addif', bridge_name, iface], check=True)
                subprocess.run(['sudo', 'ip', 'link', 'set', iface, 'up'], check=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', bridge_name, 'up'], check=True)
            return True
        elif action == 'delete':
            subprocess.run(['sudo', 'ip', 'link', 'set', bridge_name, 'down'], check=True)
            subprocess.run(['sudo', 'brctl', 'delbr', bridge_name], check=True)
            for iface in interfaces:
                subprocess.run(['sudo', 'ip', 'link', 'set', iface, 'up'], check=True)
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Bridge operation failed: {e}")
        return False

def parse_snort_alert(alert_line):
    """Parse Snort alert from unified2 format"""
    pattern = r'\[(?P<timestamp>.*?)\] \[(?P<classification>.*?)\] ' \
             r'(?P<message>.*?) {(?P<protocol>.*?)} ' \
             r'(?P<src_ip>\d+\.\d+\.\d+\.\d+):(?P<src_port>\d+) -> ' \
             r'(?P<dst_ip>\d+\.\d+\.\d+\.\d+):(?P<dst_port>\d+)'
    
    match = re.match(pattern, alert_line)
    if match:
        return {
            'timestamp': datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S.%f'),
            'classification': match.group('classification'),
            'message': match.group('message'),
            'protocol': match.group('protocol'),
            'source_ip': match.group('src_ip'),
            'source_port': match.group('src_port'),
            'destination_ip': match.group('dst_ip'),
            'destination_port': match.group('dst_port')
        }
    return None

def monitor_snort_alerts(alert_file='/var/log/snort/alert'):
    """Monitor Snort alert file and update database"""
    try:
        with open(alert_file, 'r') as f:
            for line in f:
                alert_data = parse_snort_alert(line)
                if alert_data:
                    SnortAlert.objects.create(**alert_data)
    except Exception as e:
        logger.error(f"Error monitoring Snort alerts: {e}")

def get_bridge_status(bridge_name='br0'):
    """Get current bridge status"""
    try:
        result = subprocess.run(['brctl', 'show', bridge_name], 
                              capture_output=True, text=True, check=True)
        interfaces = re.findall(r'eth\d+|wlan\d+', result.stdout)
        return {
            'active': True,
            'interfaces': interfaces
        }
    except subprocess.CalledProcessError:
        return {
            'active': False,
            'interfaces': []
        }

def manage_snort_service(action):
    """Manage Snort service"""
    try:
        subprocess.run(['sudo', 'systemctl', action, 'snort'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Snort service operation failed: {e}")
        return False

def get_snort_stats():
    """Get Snort statistics"""
    try:
        alerts = SnortAlert.objects.all()
        return {
            'total_alerts': alerts.count(),
            'high_priority': alerts.filter(priority=1).count(),
            'medium_priority': alerts.filter(priority=2).count(),
            'low_priority': alerts.filter(priority=3).count(),
            'recent_alerts': alerts.order_by('-timestamp')[:10]
        }
    except Exception as e:
        logger.error(f"Error getting Snort stats: {e}")
        return None

def validate_bridge_config(interfaces):
    """Validate bridge configuration"""
    if len(interfaces) < 2:
        return False, "At least two interfaces are required"
    
    for iface in interfaces:
        if not NetworkInterface.objects.filter(name=iface).exists():
            return False, f"Interface {iface} not found"
    
    return True, None

class SnortRuleManager:
    """Manage Snort rules"""
    def __init__(self, rules_path='/etc/snort/rules'):
        self.rules_path = rules_path

    def add_rule(self, rule_content):
        with open(f"{self.rules_path}/local.rules", 'a') as f:
            f.write(f"\n{rule_content}")
        return self.reload_snort()

    def remove_rule(self, rule_content):
        with open(f"{self.rules_path}/local.rules", 'r') as f:
            rules = f.readlines()
        
        with open(f"{self.rules_path}/local.rules", 'w') as f:
            for rule in rules:
                if rule.strip() != rule_content.strip():
                    f.write(rule)
        return self.reload_snort()

    def reload_snort(self):
        return manage_snort_service('restart')