from django.db import models

class NetworkInterface(models.Model):
    name = models.CharField(max_length=50)
    is_bridged = models.BooleanField(default=False)
    mac_address = models.CharField(max_length=17)
    ip_address = models.GenericIPAddressField(null=True)

class BridgeConfiguration(models.Model):
    name = models.CharField(max_length=50)
    interfaces = models.ManyToManyField(NetworkInterface)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class SnortAlert(models.Model):
    timestamp = models.DateTimeField()
    priority = models.IntegerField()
    classification = models.CharField(max_length=100)
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    message = models.TextField()
    packet_data = models.TextField(null=True)

class SnortRule(models.Model):
    rule_content = models.TextField()
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
# Create your models here.
