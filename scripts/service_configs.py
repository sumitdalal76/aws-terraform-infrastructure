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
            "--query", "Buckets[].[CreationDate,Name]",
            "--output", "text"
        ]
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
            "--filters", "Name=is-default,Values=false",
            "--query", """
            Vpcs[].[
                VpcId,
                Tags[?Key=='Name'].Value | [0] || 'Unnamed',
                CidrBlock,
                State,
                DhcpOptionsId,
                (RouteTableIds || ''),
                (SubnetIds || ''),
                (FlowLogs || '')
            ]
            """,
            "--output", "text"
        ]
    }
}