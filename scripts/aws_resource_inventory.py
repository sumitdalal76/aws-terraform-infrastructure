import subprocess
from rich.console import Console
from rich.table import Table

# Initialize console for better terminal output
console = Console()

def run_aws_command(command_list):
    """
    Generic function to run AWS CLI commands
    """
    try:
        result = subprocess.run(
            command_list,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error running AWS command: {str(e)}[/bold red]")
        return ""

def get_regions():
    """
    Get list of AWS regions
    """
    return run_aws_command([
        "aws", "ec2", "describe-regions",
        "--query", "Regions[].RegionName",
        "--output", "text"
    ]).split()

def scan_service(service_config):
    """
    Generic function to scan AWS services
    """
    try:
        table = Table(title=f"AWS {service_config['title']}")
        
        # Add columns to table
        for col in service_config['columns']:
            table.add_column(col['header'], style=col.get('style', 'white'))
        
        if service_config.get('regional', False):
            # For regional services, scan each region
            regions = get_regions()
            for region in regions:
                command = service_config['command'](region)
                output = run_aws_command(command)
                
                if output:
                    # Process output
                    for line in output.split('\n'):
                        if line and not line.isspace():
                            values = line.strip().split('\t')
                            if len(values) >= len(service_config['columns']) - 1:  # -1 for region
                                table.add_row(region, *values)
                else:
                    console.print(f"[bold yellow]No resources found in {region}[/bold yellow]")
        else:
            # For global services
            command = service_config['command']()
            output = run_aws_command(command)
            
            # Process output
            for line in output.split('\n'):
                if line and not line.isspace():
                    values = line.strip().split(' ', 1)
                    if len(values) >= len(service_config['columns']):
                        table.add_row(*values)
        
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error scanning {service_config['title']}: {str(e)}[/bold red]")

# Service configurations
SERVICE_CONFIGS = {
    's3': {
        'title': 'S3 Buckets',
        'regional': False,
        'columns': [
            {'header': 'Creation Date', 'style': 'cyan'},
            {'header': 'Bucket Name', 'style': 'green'}
        ],
        'command': lambda: ["aws", "s3", "ls"]
    },
    'vpc': {
        'title': 'VPCs',
        'regional': True,
        'columns': [
            {'header': 'Region', 'style': 'blue'},
            {'header': 'VPC ID', 'style': 'cyan'},
            {'header': 'CIDR Block', 'style': 'green'},
            {'header': 'State', 'style': 'yellow'}
        ],
        'command': lambda region: [
            "aws", "ec2", "describe-vpcs",
            "--region", region,
            "--output", "text",
            "--query", "Vpcs[].[VpcId,CidrBlock,State]"
        ]
    }
    # Add more services here following the same pattern
}

def scan_aws_resources(services=None):
    """
    Main function to scan AWS resources
    """
    if services is None:
        services = SERVICE_CONFIGS.keys()
    
    for service in services:
        if service in SERVICE_CONFIGS:
            console.print(f"\n[bold cyan]Scanning {SERVICE_CONFIGS[service]['title']}...[/bold cyan]")
            scan_service(SERVICE_CONFIGS[service])
        else:
            console.print(f"[bold red]Service {service} not configured[/bold red]")

if __name__ == "__main__":
    # Scan specific services
    scan_aws_resources(['s3', 'vpc'])
    
    # Or scan all configured services
    # scan_aws_resources()
