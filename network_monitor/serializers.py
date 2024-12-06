# serializers.py
from rest_framework import serializers
from .models import NetworkInterface, SnortAlert, SnortRule, BridgeConfiguration

class NetworkInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkInterface
        fields = ['id', 'name', 'mac_address', 'ip_address', 'is_bridged']

class SnortAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SnortAlert
        fields = ['id', 'timestamp', 'priority', 'classification', 
                 'source_ip', 'destination_ip', 'message', 'packet_data']

class SnortRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SnortRule
        fields = ['id', 'rule_content', 'is_active', 'category', 'created_at']

class BridgeConfigurationSerializer(serializers.ModelSerializer):
    interfaces = NetworkInterfaceSerializer(many=True, read_only=True)

    class Meta:
        model = BridgeConfiguration
        fields = ['id', 'name', 'interfaces', 'is_active', 'created_at']