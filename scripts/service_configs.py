# AWS CLI commands for each service
#https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ec2/describe-vpcs.html
AWS_COMMANDS = {
    's3': {
        'command': lambda: ["aws", "s3", "ls"],
        'regional': False,
        'columns': ['Creation Date', 'Bucket Name']
    },
    'vpc': {
        'command': lambda region: ["aws", "ec2", "describe-vpcs", "--region", region, "--filters", "Name=is-default,Values=false", "--query", "Vpcs[].[VpcId,Tags[?Key=='Name'].Value|[0],CidrBlock,State,IsDefault,OwnerId]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'VPC ID', 'Name', 'CIDR Block', 'State', 'IsDefault', 'Owner ID']
    },
    'ec2': {
        'command': lambda region: ["aws", "ec2", "describe-instances", "--region", region, "--filters", "Name=instance-state-name,Values=running,stopped", "--query", "Reservations[].Instances[].[InstanceId,InstanceType,State.Name]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Instance ID', 'Type', 'State']
    },
    'rds': {
        'command': lambda region: ["aws", "rds", "describe-db-instances", "--region", region, "--output", "text"],
        'regional': True,
        'columns': ['Region', 'DB ID', 'Status']
    },
    'lambda': {
        'command': lambda region: ["aws", "lambda", "list-functions", "--region", region, "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Function Name', 'Runtime']
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