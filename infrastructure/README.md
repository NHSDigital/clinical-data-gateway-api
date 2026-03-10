# Infrastructure

Terraform configurations, Docker images, and environment definitions for deploying the Clinical Data Gateway API to AWS.

## Project Structure

```text
infrastructure/
├── environments/                          # Terraform root modules, one per environment
│   ├── dev/                               # Development environment (placeholder)
│   └── preview/                           # Preview environment — per-branch deployments
│       ├── terraform.tf                   # Provider and S3 backend configuration
│       ├── main.tf                        # Resources: ALB rule, ECS service, CloudWatch, etc.
│       ├── variables.tf                   # Input variables (branch_name, image_tag, domain, etc.)
│       ├── outputs.tf                     # Outputs: preview URL, target group ARN, ECS service name
│       └── preview.tfvars                 # Default variable values for the preview environment
├── images/                                # Docker image definitions
│   ├── build-container/                   # CI/CD build container (Python, asdf, linters, Docker CLI)
│   │   ├── Dockerfile
│   │   └── resources/                     # Files copied into the build container
│   └── gateway-api/                       # Gateway API runtime container (Python + Flask on Alpine)
│       ├── Dockerfile
│       └── resources/                     # Application code copied into the runtime container
└── modules/                               # Reusable Terraform modules (placeholder)
```

## Environments

### Preview

The `preview/` environment creates an isolated, per-branch deployment of the Gateway API. Each PR gets its own ECS service, ALB target group rule, and DNS record under `dev.endpoints.clinical-data-gateway.national.nhs.uk`.

Key input variables:

| Variable | Description | Default |
|---|---|---|
| `branch_name` | Git branch name — used to derive the hostname and resource names | *(required)* |
| `image_tag` | Docker image tag to deploy; defaults to `branch_name` if empty | `""` |
| `base_domain` | Base domain for the preview URL | `dev.endpoints.clinical-data-gateway.national.nhs.uk` |
| `container_port` | Port the container listens on | `8080` |
| `desired_count` | Number of ECS tasks | `1` |

In CI, the Terraform state key is set per branch (e.g. `dev/preview/<branch>.tfstate`) so each preview environment has its own isolated state.

```bash
# Typical CI usage
terraform init -backend-config="key=dev/preview/${BRANCH_NAME}.tfstate"
terraform apply -var="branch_name=${BRANCH_NAME}" -var="image_tag=${IMAGE_TAG}"
```

### Dev

The `dev/` environment is currently a placeholder for the shared development environment.

## Docker Images

### `gateway-api`

A lightweight Alpine-based Python image that runs the Flask application. Built with:

- A configurable `PYTHON_VERSION` build argument
- A non-root user (`gateway_api_user`)
- Stubs enabled by default (`STUB_PDS`, `STUB_SDS`, `STUB_PROVIDER` all set to `true`)
- Flask listening on `0.0.0.0:8080`

### `build-container`

A dev container image used by CI/CD pipelines, based on the VS Code Alpine base image. Includes:

- Python (via asdf)
- Docker CLI and Buildx
- Linters and checkers: vale, hadolint (via npm/markdownlint), ShellCheck
- Development certificate support for machines behind corporate proxies

## Terraform Operations

Terraform is managed through the Make targets defined in `scripts/terraform/terraform.mk`:

```bash
make terraform-init    dir=infrastructure/environments/preview
make terraform-plan    dir=infrastructure/environments/preview
make terraform-apply   dir=infrastructure/environments/preview
make terraform-destroy dir=infrastructure/environments/preview
```

These wrap the `scripts/terraform/terraform.sh` script, which runs Terraform natively or falls back to a Docker container.
