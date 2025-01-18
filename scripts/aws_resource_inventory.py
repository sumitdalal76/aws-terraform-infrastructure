import subprocess
import json
from rich.console import Console
from rich.table import Table
from service_configs import SERVICE_CONFIGS, SERVICES_TO_SCAN

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
        results = []
        
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
                            table.add_row(region, line.strip())
                            results.append({
                                'Region': region,
                                'Output': line.strip()
                            })
        else:
            # For global services like S3
            command = service_config['command']()
            output = run_aws_command(command)
            
            # Process output
            for line in output.split('\n'):
                if line and not line.isspace():
                    table.add_row(line.strip())
                    results.append({
                        'Output': line.strip()
                    })
        
        console.print(table)
        return results

    except Exception as e:
        console.print(f"[bold red]Error scanning {service_config['title']}: {str(e)}[/bold red]")
        return []

def scan_aws_resources(services=None):
    """
    Main function to scan AWS resources
    """
    if services is None:
        services = SERVICE_CONFIGS.keys()
    
    all_results = {}
    
    for service in services:
        if service in SERVICE_CONFIGS:
            console.print(f"\n[bold cyan]Scanning {SERVICE_CONFIGS[service]['title']}...[/bold cyan]")
            results = scan_service(SERVICE_CONFIGS[service])
            all_results[service] = results
        else:
            console.print(f"[bold red]Service {service} not configured[/bold red]")
    
    # Save results to file
    with open('aws_inventory.json', 'w') as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    scan_aws_resources(SERVICES_TO_SCAN)
