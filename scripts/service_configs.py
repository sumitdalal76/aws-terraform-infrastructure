# Just list the services you want to scan
SERVICES_TO_SCAN = ['s3', 'ec2']

# Basic configuration that works for any service
def get_service_config(service_name):
    """
    Get basic configuration for any AWS service
    """
    if service_name == 's3':
        return {
            'title': 'S3 Buckets',
            'regional': False,
            'command': lambda: ["aws", "s3", "ls"]
        }
    else:
        return {
            'title': f'{service_name.upper()}',
            'regional': True,
            'command': lambda region: [
                "aws", service_name, "describe-" + service_name + "s",
                "--region", region,
                "--output", "text"
            ]
        }

# Generate configs for all services
SERVICE_CONFIGS = {service: get_service_config(service) for service in SERVICES_TO_SCAN}