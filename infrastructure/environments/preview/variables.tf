variable "branch_name" {
  description = "The name of the branch for the preview environment."
  type        = string
}

variable "base_domain" {
  description = "The base domain for the preview environment."
  type        = string
  default     = "dev.endpoints.clinical-data-gateway.national.nhs.uk"
}

variable "image_tag" {
  description = "The Docker image tag to deploy to ECS."
  type        = string
  default     = ""
}

variable "container_port" {
  description = "The port on which the container listens."
  type        = number
  default     = 8080
}

variable "desired_count" {
  description = "The desired number of ECS tasks."
  type        = number
  default     = 1
}

variable "alb_rule_priority" {
  description = "The priority for the ALB listener rule."
  type        = number
}

variable "cpu" {
  description = "The CPU units (1 cpu = 1000) for the ECS task."
  type        = number
  default     = 256
}

variable "memory" {
  description = "The memory (in MiB) for the ECS task."
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch Logs for the preview task."
  type        = number
  default     = 14
}

variable "log_kms_key_id" {
  description = "KMS CMK ARN or ID used to encrypt the CloudWatch log group."
  type        = string
  default     = null
}

variable "provider_url" {
  description = "The URL of the provider service to connect to."
  type        = string
  default     = "https://provider.dev.endpoints.clinical-data-gateway.national.nhs.uk"
}

variable "provider_mtls_cert" {
  description = "Name of the secret containing the client certificate for mTLS authentication with the provider."
  type        = string
  default     = null
}

variable "provider_mtls_key" {
  description = "Name of the secret containing the private key for mTLS authentication with the provider."
  type        = string
  default     = null
}

variable "sds_url" {
  description = "The URL of the SDS service to connect to."
  type        = string
  default     = null
}

variable "sds_api_token" {
  description = "API token used to authenticate with SDS."
  type        = string
  default     = null
}

variable "pds_url" {
  description = "The URL of the PDS service to connect to."
  type        = string
  default     = null
}

variable "pds_api_token" {
  description = "API token used to authenticate with PDS."
  type        = string
  default     = null
}

variable "pds_api_secret" {
  description = "API secret used to authenticate with PDS."
  type        = string
  default     = null
}

