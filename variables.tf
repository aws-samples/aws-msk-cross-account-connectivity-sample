variable "iam_instance_profile_arn" {
  type = string
}

variable "clusterlist" {
  type    = list(string)
  default = []
}

variable "confluent_package_filename" {
  type = string
}

variable "binaries_s3_bucket" {
  type = string
}

variable "num_brokers" {
  type    = number
  default = 3
}

variable "msk_ami_account_id" {
  type = string
}

variable "msk_kafka_version" {
  type    = string
  default = "2.6.2"
}

variable "msk_instance_type" {
  type    = string
  default = "kafka.m5.large"
}

variable "msk_ebs_volume_size" {
  type    = number
  default = 50
}