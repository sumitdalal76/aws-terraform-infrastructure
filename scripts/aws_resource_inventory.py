import subprocess
import json
from rich.console import Console
from rich.table import Table
from service_configs import AWS_COMMANDS

# Initialize console for output
console = Console()

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
        console.print(f"Error running AWS command: {str(e)}")
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
        table = Table(
            title=f"AWS {service_config['title']}", 
            show_header=True,
            expand=True
        )
        results = []
        
        # Add columns from service config
        for col in service_config['columns']:
            table.add_column(col, no_wrap=False, justify="left")
        
        if service_config.get('regional', False):
            regions = get_regions()
            has_resources = False
            for region in regions:
                command = service_config['command'](region)
                output = run_aws_command(command)
                
                if output:
                    for line in output.split('\n'):
                        if line and not line.isspace():
                            has_resources = True
                            values = [item.strip() for item in line.strip().split('\t')]
                            table.add_row(region, *values)
                            results.append({
                                'Region': region,
                                'Output': line.strip()
                            })
            
            if not has_resources:
                table.add_row("No resources found", *[""] * (len(service_config['columns']) - 1))
        else:
            command = service_config['command']()
            output = run_aws_command(command)
            
            if output:
                for line in output.split('\n'):
                    if line and not line.isspace():
                        values = [item.strip() for item in line.strip().split()]
                        table.add_row(*values)
                        results.append({
                            'Output': line.strip()
                        })
            else:
                table.add_row("No resources found", *[""] * (len(service_config['columns']) - 1))
        
        console.print(table)
        return results

    except Exception as e:
        console.print(f"Error scanning {service_config['title']}: {str(e)}")
        return []

def scan_aws_resources():
    """
    Main function to scan AWS resources
    """
    all_results = {}
    
    for service in AWS_COMMANDS.keys():
        config = get_service_config(service)
        console.print(f"\nScanning {config['title']}...")
        results = scan_service(config)
        all_results[service] = results
    
    # Save results to file
    with open('aws_inventory.json', 'w') as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    scan_aws_resources()
