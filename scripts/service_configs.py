# AWS CLI commands for each service
AWS_COMMANDS = {
    's3': {
        'command': lambda: ["aws", "s3", "ls"],
        'regional': False
    },
    'vpc': {
        'command': lambda region: ["aws", "ec2", "describe-vpcs", "--region", region, "--query", "Vpcs[].[VpcId,Tags[?Key=='Name'].Value|[0],CidrBlock,State,IsDefault,OwnerId]", "--output", "text"],
        'regional': True
    },
    'ec2': {
        'command': lambda region: ["aws", "ec2", "describe-instances", "--region", region, "--output", "text"],
        'regional': True
    },
    'rds': {
        'command': lambda region: ["aws", "rds", "describe-db-instances", "--region", region, "--output", "text"],
        'regional': True
    },
    'lambda': {
        'command': lambda region: ["aws", "lambda", "list-functions", "--region", region, "--output", "text"],
        'regional': True
    }
}

def get_service_config(service_name):
    """
    Get configuration for any AWS service
    """
    if service_name not in AWS_COMMANDS:
        raise ValueError(f"Service {service_name} not configured. Please add it to AWS_COMMANDS.")
    
    return {
        'title': f'{service_name.upper()}',
        **AWS_COMMANDS[service_name]  # Unpacks command and regional settings
    }

# Generate configs for all services
SERVICE_CONFIGS = {service: get_service_config(service) for service in AWS_COMMANDS.keys()}