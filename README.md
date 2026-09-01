# MiniTeams

MiniTeams is a cloud-hosted real-time chat application built to demonstrate containerized application deployment, Infrastructure as Code, AWS networking, persistent data storage, and WebSocket communication.

The application allows multiple users to join a shared chat room and exchange messages in real time. The application is containerized with Docker and deployed to AWS ECS Fargate behind an Application Load Balancer, with DynamoDB providing persistent message storage.

The entire AWS environment is defined using Terraform and can be created or destroyed from code.

---

## Project Goals

MiniTeams was built as a hands-on cloud engineering project rather than as a production replacement for Microsoft Teams or Slack.

The primary goals were to:

- Build a real-time application using WebSockets
- Containerize an application with Docker
- Deploy containers using Amazon ECS Fargate
- Provision AWS infrastructure using Terraform
- Configure networking across multiple Availability Zones
- Expose a containerized application through an Application Load Balancer
- Persist application data using DynamoDB
- Implement IAM roles using least-privilege principles
- Centralize application logs in CloudWatch
- Validate that the entire environment can be destroyed and recreated from code

---

## Architecture

MiniTeams uses the following request flow:

```text
                    Internet
                       |
                       v
          Application Load Balancer
                HTTP / WebSocket
                       |
                       v
                ECS Fargate
              FastAPI Container
                  /        \
                 /          \
                v            v
          DynamoDB       CloudWatch
          Messages          Logs
```

The supporting infrastructure is deployed inside a custom AWS VPC:

```text
AWS Region: us-east-1

┌──────────────────────────────────────────────────────────┐
│ VPC                                                      │
│                                                          │
│   ┌──────────────────┐      ┌──────────────────┐         │
│   │ Public Subnet A  │      │ Public Subnet B  │         │
│   │   us-east-1a     │      │   us-east-1b     │         │
│   └──────────────────┘      └──────────────────┘         │
│            │                         │                    │
│            └───────────┬─────────────┘                    │
│                        │                                  │
│               Application Load                           │
│                   Balancer                               │
│                        │                                  │
│                        v                                  │
│                  ECS Fargate                             │
│                   Task :8000                             │
│                                                          │
└──────────────────────────┬───────────────────────────────┘
                           │
                           v
                       DynamoDB
```

The Application Load Balancer spans two public subnets in separate Availability Zones. The ECS security group only permits application traffic on port `8000` from the ALB security group.

The ECS task is assigned a public IP for outbound connectivity, avoiding the cost and additional complexity of a NAT Gateway for this project.

---

## Technologies

| Technology | Purpose |
|---|---|
| AWS ECS Fargate | Runs the containerized application |
| Amazon ECR | Stores the Docker image |
| Application Load Balancer | Routes HTTP and WebSocket traffic to ECS |
| Amazon DynamoDB | Persists chat messages |
| Amazon CloudWatch | Stores ECS application logs |
| AWS IAM | Provides ECS execution and application permissions |
| Amazon VPC | Provides networking and security boundaries |
| Terraform | Provisions and manages AWS infrastructure |
| Docker | Packages the application and its dependencies |
| FastAPI | Python application backend |
| WebSockets | Provides real-time bidirectional messaging |
| JavaScript | Handles browser-side chat behavior |
| HTML/CSS | Provides the web interface |

---

## How MiniTeams Works

### Real-Time Messaging

When a browser loads MiniTeams, the frontend establishes a persistent WebSocket connection with the FastAPI backend.

When a user sends a message:

1. The browser sends the message through the WebSocket connection.
2. FastAPI receives and validates the message.
3. The backend writes the message to DynamoDB.
4. FastAPI broadcasts the message to connected WebSocket clients.
5. Connected browsers immediately render the new message.

This allows users in multiple browser sessions to communicate without repeatedly polling the server.

---

## Message Persistence

Messages are stored in DynamoDB rather than in the ECS container.

Each message contains information such as:

```text
roomId
messageId
sender
content
createdAt
```

The application currently uses a shared `GENERAL` room.

The DynamoDB table uses:

```text
Partition Key: roomId
Sort Key:      messageId
```

The message ID contains timestamp information along with a unique identifier, allowing messages within a room to be uniquely identified and ordered.

Because messages are externalized to DynamoDB, chat history survives:

- Browser refreshes
- Container restarts
- ECS task replacements
- Application deployments

---

## WebSocket Design

MiniTeams uses WebSockets for persistent bidirectional communication between browsers and the FastAPI application.

The Application Load Balancer handles both standard HTTP requests and WebSocket upgrade requests and forwards them to the ECS task.

The current implementation intentionally runs:

```text
desired_count = 1
```

for the ECS service.

Connected WebSocket clients are tracked in application memory. Running multiple ECS tasks would therefore create separate groups of WebSocket connections, and a message received by one task would not automatically be broadcast to clients connected to another task.

A horizontally scaled version could introduce a shared messaging layer such as Redis/ElastiCache or another publish/subscribe system to distribute messages between application instances.

This limitation was intentionally left outside the scope of the project.

---

## Infrastructure as Code

All AWS infrastructure is defined using Terraform.

Terraform provisions resources including:

- VPC
- Public subnets across two Availability Zones
- Internet Gateway
- Route tables
- Security groups
- Application Load Balancer
- Target group
- ALB listener
- ECS cluster
- ECS Fargate service
- ECS task definition
- ECR repository
- DynamoDB table
- IAM roles and policies
- CloudWatch log group

This allows the environment to be recreated without manually configuring resources through the AWS Console.

---

## IAM Design

MiniTeams separates ECS infrastructure permissions from application permissions.

### ECS Task Execution Role

The ECS task execution role allows ECS to perform infrastructure-level operations such as:

- Pulling the MiniTeams image from ECR
- Sending container logs to CloudWatch

### Application Task Role

The application receives a separate IAM task role that permits the FastAPI application to interact with the MiniTeams DynamoDB table.

The application does not require hard-coded AWS access keys when running in ECS. AWS credentials are provided to the container through the ECS task role.

---

## Network Security

MiniTeams uses separate security groups for the load balancer and application.

### ALB Security Group

Allows inbound HTTP traffic:

```text
Internet
   |
TCP 80
   |
   v
Application Load Balancer
```

### ECS Security Group

The ECS task does **not** accept application traffic directly from the internet.

Port `8000` is only accessible from the Application Load Balancer security group:

```text
Internet
   |
   v
ALB Security Group
   |
TCP 8000
   |
   v
ECS Security Group
```

This ensures application traffic reaches the container through the load balancer.

---

## Health Checks

The FastAPI application provides:

```http
GET /health
```

The Application Load Balancer uses this endpoint to determine whether the ECS task is healthy and able to receive traffic.

Example response:

```json
{
  "status": "ok"
}
```

---

## Logging

ECS container logs are sent to Amazon CloudWatch Logs.

The application uses the CloudWatch log group:

```text
/ecs/miniteams
```

This allows application startup events, HTTP requests, WebSocket activity, and errors to be inspected without connecting directly to the container.

---

# Running MiniTeams Locally

## Prerequisites

Install:

- Git
- Docker
- Docker Compose
- AWS CLI

Because the current application persists messages to DynamoDB, a DynamoDB table and valid AWS credentials are required for full message functionality.

---

## Clone the Repository

```bash
git clone https://github.com/richardmorales27/miniTeams.git

cd miniTeams
```

---

## Start with Docker Compose

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000
```

To test real-time messaging, open MiniTeams in two browser windows and use a different display name in each window.

Messages sent from one window should immediately appear in the other.

Stop the application with:

```bash
docker compose down
```

---

# Deploying to AWS

> AWS resources created by this project may incur charges. Review the Terraform configuration and AWS pricing before deployment.

## 1. Initialize Terraform

```bash
cd terraform

terraform init
```

---

## 2. Review the Infrastructure

```bash
terraform plan
```

Review the resources Terraform intends to create.

---

## 3. Deploy the Infrastructure

```bash
terraform apply
```

Confirm the deployment when prompted.

Terraform creates the AWS infrastructure, including the ECR repository.

---

## 4. Retrieve the ECR Repository

```bash
ECR_REPO=$(terraform output -raw ecr_repository_url)
```

---

## 5. Build the MiniTeams Container

Return to the project root:

```bash
cd ..
```

Build the image:

```bash
docker build -t miniteams .
```

---

## 6. Authenticate Docker with ECR

```bash
aws ecr get-login-password --region us-east-1 \
  | docker login \
  --username AWS \
  --password-stdin \
  $(echo $ECR_REPO | cut -d/ -f1)
```

---

## 7. Tag the Image

```bash
docker tag miniteams:latest $ECR_REPO:latest
```

---

## 8. Push the Image to ECR

```bash
docker push $ECR_REPO:latest
```

---

## 9. Deploy the New Image

Because the ECS service may initially start before the first image has been pushed to a newly created ECR repository, force a new deployment after the image is available:

```bash
aws ecs update-service \
  --cluster miniteams-cluster \
  --service miniteams-service \
  --force-new-deployment \
  --region us-east-1
```

Wait for the ECS service to become healthy.

---

## 10. Retrieve the Application URL

```bash
cd terraform

terraform output -raw miniteams_url
```

Open the returned URL in a browser.

---

# Destroying the Environment

MiniTeams was designed so the AWS environment can be destroyed when it is not being demonstrated.

Before destroying the infrastructure, scale the ECS service to zero:

```bash
aws ecs update-service \
  --cluster miniteams-cluster \
  --service miniteams-service \
  --desired-count 0 \
  --region us-east-1
```

Verify that no tasks remain:

```bash
aws ecs describe-services \
  --cluster miniteams-cluster \
  --services miniteams-service \
  --region us-east-1 \
  --query 'services[0].[desiredCount,runningCount,pendingCount]' \
  --output table
```

Wait until the service reports:

```text
desired: 0
running: 0
pending: 0
```

Then destroy the environment:

```bash
terraform destroy
```

Scaling the service down first gives AWS time to release the Fargate network interface before Terraform removes the VPC and Internet Gateway.

---

# Project Structure

```text
miniTeams/
├── Dockerfile
├── README.md
├── docker-compose.yml
│
├── app/
│   ├── main.py
│   ├── requirements.txt
│   │
│   └── static/
│       ├── app.js
│       ├── index.html
│       └── styles.css
│
└── terraform/
    ├── alb.tf
    ├── dynamodb.tf
    ├── ecr.tf
    ├── ecs.tf
    ├── iam.tf
    ├── main.tf
    ├── networking.tf
    ├── outputs.tf
    ├── security-groups.tf
    └── variables.tf
```

---

# Validation Performed

The completed deployment was tested for:

- Successful Terraform infrastructure deployment
- Successful Docker image build
- Successful ECR image push
- Healthy ECS Fargate deployment
- ALB health checks
- Public application access
- WebSocket connections through the ALB
- Real-time messaging between multiple browser sessions
- DynamoDB message persistence
- Message persistence after browser refresh
- Message persistence after ECS task replacement
- CloudWatch container logging
- Complete Terraform destruction
- Complete infrastructure reconstruction from Terraform

The final reproducibility test destroyed the AWS environment and rebuilt it from the Terraform configuration before validating the application again.

---

# Challenges and Lessons Learned

## WebSocket State and Horizontal Scaling

WebSocket connections remain attached to individual application instances. This means adding additional ECS tasks would require a shared messaging mechanism to distribute events between tasks.

For the current scope, MiniTeams deliberately uses a single ECS task.

## Container Persistence

Application containers are ephemeral. Storing messages inside the FastAPI process would cause history to disappear whenever an ECS task was replaced.

Moving message storage to DynamoDB separated application compute from application state.

## ECS Networking During Teardown

During infrastructure testing, an ECS Fargate Elastic Network Interface remained attached while Terraform attempted to remove the Internet Gateway.

The deployment workflow was adjusted to scale the ECS service to zero and allow AWS to release the task ENI before destroying the remaining network infrastructure.

## Reproducible Infrastructure

Destroying and rebuilding the entire environment demonstrated that the project does not depend on manually configured AWS resources.

The infrastructure can be reconstructed from Terraform and the application container.

---

# Future Improvements

MiniTeams intentionally remains small in scope, but a production-oriented version could include:

- User authentication
- Multiple chat rooms
- Redis/ElastiCache-backed WebSocket pub/sub
- Multiple ECS tasks and autoscaling
- HTTPS with ACM
- Custom domain
- Message pagination
- Presence indicators
- Direct messages
- File attachments
- CI/CD deployment pipeline
- Automated infrastructure and application testing
- Improved frontend user experience

These features were intentionally left outside the scope of this project so MiniTeams could remain focused on its primary cloud engineering objectives.

---

# What This Project Demonstrates

MiniTeams demonstrates practical experience with:

**Cloud Engineering**
- AWS networking
- ECS/Fargate
- Load balancing
- IAM
- DynamoDB
- ECR
- CloudWatch

**Infrastructure as Code**
- Terraform resource provisioning
- Infrastructure dependencies
- Repeatable deployment and destruction

**Containers**
- Docker image creation
- Local Docker Compose development
- Container registry workflows
- ECS container deployment

**Application Architecture**
- FastAPI
- REST endpoints
- WebSockets
- Persistent application state
- Real-time client/server communication

**Operations**
- Health checks
- Centralized logging
- ECS task replacement
- Infrastructure troubleshooting
- Full environment reconstruction

---

## Author

**Richard Morales**

Cloud / Infrastructure Engineering Portfolio Project