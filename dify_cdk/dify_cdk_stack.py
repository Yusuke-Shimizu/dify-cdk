from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput,
    CfnParameter,
)
from constructs import Construct
import os
import json

class DifyCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 環境変数から複数のIPアドレスを取得
        allowed_ips_str = os.environ.get('ALLOWED_IPS', '')
        
        # 環境変数が設定されていない場合はCloudFormationパラメータを使用
        if not allowed_ips_str:
            allowed_ips_param = CfnParameter(
                self, "AllowedIPs",
                type="String",
                description="Comma-separated list of IP addresses with CIDR notation (e.g., 123.123.123.123/32,124.124.124.124/32)",
                default="0.0.0.0/0"  # デフォルトは全開放（本番環境では避けるべき）
            )
            allowed_ips_str = allowed_ips_param.value_as_string
        
        # カンマ区切りの文字列をリストに変換
        allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]
        
        # CIDRブロック形式になっていない場合は追加
        for i, ip in enumerate(allowed_ips):
            if '/' not in ip:
                allowed_ips[i] = f"{ip}/32"
        
        # IPが指定されていない場合は全開放
        if not allowed_ips:
            allowed_ips = ["0.0.0.0/0"]

        # VPCの作成
        vpc = ec2.Vpc(
            self, "DifyVPC",
            ip_addresses=ec2.IpAddresses.cidr("192.168.0.0/16"),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=20
                )
            ],
            nat_gateways=0
        )

        # セキュリティグループの作成
        security_group = ec2.SecurityGroup(
            self, "DifySecurityGroup",
            vpc=vpc,
            description="Allow HTTP traffic from specific IPs",
            allow_all_outbound=True
        )

        # 複数のIPからのHTTPアクセスを許可
        for i, ip in enumerate(allowed_ips):
            security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(ip),
                connection=ec2.Port.tcp(80),
                description=f"Allow HTTP traffic from {ip}"
            )

        # IAMロールの作成
        role = iam.Role(
            self, "DifyWsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
            ]
        )

        # EC2インスタンスの作成
        instance = ec2.Instance(
            self, "DifyWsInstance",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
            machine_image=ec2.MachineImage.from_ssm_parameter(
                "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64",
                os=ec2.OperatingSystemType.LINUX
            ),
            security_group=security_group,
            role=role,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=20,
                        encrypted=True
                    )
                )
            ],
            user_data=ec2.UserData.custom('''#!/bin/bash
max_attempts=5
attempt_num=1
success=false
while [ $success = false ] && [ $attempt_num -le $max_attempts ]; do
  sudo dnf install -y git docker
  if [ $? -eq 0 ]; then
    echo "dnf install succeeded"
    success=true
  else
    echo "dnf install $attempt_num failed. trying again..."
    sleep 3
    ((attempt_num++))
  fi
done

sudo systemctl start docker
sudo gpasswd -a ec2-user docker
sudo gpasswd -a ssm-user docker
sudo chgrp docker /var/run/docker.sock
sudo service docker restart
sudo systemctl enable docker
sudo curl -L "https://github.com/docker/compose/releases/download/v2.28.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
cd /opt
sudo git clone https://github.com/langgenius/dify.git
cd /opt/dify
sudo git checkout 0.9.1-fix1
sudo git pull origin 0.9.1-fix1
cd /opt/dify/docker
sudo cp .env.example .env
docker-compose up -d
''')
        )

        # アウトプットの定義
        CfnOutput(
            self, "InstancePublicIP",
            value=instance.instance_public_ip,
            export_name="DifyInstancePublicIP",
            description="Public IP of the EC2 instance"
        )

        CfnOutput(
            self, "InstanceId",
            value=instance.instance_id,
            export_name="DifyInstanceId",
            description="InstanceId of the EC2 instance"
        )
