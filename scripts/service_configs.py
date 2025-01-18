# List of services to scan
SERVICES_TO_SCAN = ['s3', 'vpc']

# Service configurations dictionary
SERVICE_CONFIGS = {
    's3': {
        'title': 'S3 Buckets',
        'regional': False,
        'columns': [
            {'header': 'Creation Date', 'style': 'cyan'},
            {'header': 'Bucket Name', 'style': 'green'},
            {'header': 'Size (Bytes)', 'style': 'yellow'},
            {'header': 'Objects Count', 'style': 'magenta'},
            {'header': 'Versioning', 'style': 'blue'},
            {'header': 'Encryption', 'style': 'red'}
        ],
        'command': lambda: [
            "aws", "s3api", "list-buckets",
            "--output", "text",
            "--query", "Buckets[].[CreationDate,Name]"
        ],
        'additional_commands': {
            'metrics': lambda bucket: [
                "aws", "s3api", "get-bucket-metrics-configuration",
                "--bucket", bucket,
                "--output", "text"
            ],
            'versioning': lambda bucket: [
                "aws", "s3api", "get-bucket-versioning",
                "--bucket", bucket,
                "--output", "text"
            ],
            'encryption': lambda bucket: [
                "aws", "s3api", "get-bucket-encryption",
                "--bucket", bucket,
                "--output", "text"
            ]
        }
    },
    'vpc': {
        'title': 'VPCs',
        'regional': True,
        'columns': [
            {'header': 'Region', 'style': 'blue'},
            {'header': 'VPC ID', 'style': 'cyan'},
            {'header': 'VPC Name', 'style': 'white'},
            {'header': 'CIDR Block', 'style': 'green'},
            {'header': 'State', 'style': 'yellow'},
            {'header': 'DHCP Options', 'style': 'magenta'},
            {'header': 'Route Tables', 'style': 'red'},
            {'header': 'Subnets', 'style': 'cyan'},
            {'header': 'Flow Logs', 'style': 'blue'}
        ],
        'command': lambda region: [
            "aws", "ec2", "describe-vpcs",
            "--region", region,
            "--output", "text",
            "--query", """
            Vpcs[?IsDefault==`false`].[
                VpcId,
                Tags[?Key=='Name'].Value | [0] || 'Unnamed',
                CidrBlock,
                State,
                DhcpOptionsId,
                EnableDnsHostnames,
                EnableDnsSupport
            ]
            """
        ],
        'additional_commands': {
            'route_tables': lambda region, vpc_id: [
                "aws", "ec2", "describe-route-tables",
                "--region", region,
                "--filters", f"Name=vpc-id,Values={vpc_id}",
                "--query", "RouteTables[].Routes[].DestinationCidrBlock",
                "--output", "text"
            ],
            'subnets': lambda region, vpc_id: [
                "aws", "ec2", "describe-subnets",
                "--region", region,
                "--filters", f"Name=vpc-id,Values={vpc_id}",
                "--query", "Subnets[].[CidrBlock,AvailabilityZone]",
                "--output", "text"
            ],
            'flow_logs': lambda region, vpc_id: [
                "aws", "ec2", "describe-flow-logs",
                "--region", region,
                "--filter", f"Name=resource-id,Values={vpc_id}",
                "--query", "FlowLogs[].LogGroupName",
                "--output", "text"
            ]
        }
    }
    # Add more services here
}