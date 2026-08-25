resource "aws_dynamodb_table" "messages" {
  name         = "${var.project_name}-messages"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "roomId"
  range_key = "messageId"

  attribute {
    name = "roomId"
    type = "S"
  }

  attribute {
    name = "messageId"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-messages"
  }
}