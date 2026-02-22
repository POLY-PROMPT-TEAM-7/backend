import asyncio
import os
from typing import Any
import uuid
import boto3
from boto3.session import Session
from botocore.exceptions import (
  BotoCoreError,
  ClientError,
  NoCredentialsError,
  PartialCredentialsError,
)

class TextractClient:

  def __init__(self, region_name: str | None = None) -> None:
    self.region_name = region_name or os.getenv("AWS_REGION") or "us-west-1"
    self.role_arn = os.getenv("AWS_ROLE_ARN")
    self.role_external_id = os.getenv("AWS_ROLE_EXTERNAL_ID")
    self.role_session_name = os.getenv(
      "AWS_ROLE_SESSION_NAME",
      "backend-placeholder-textract",
    )
    self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    self.upload_bucket = os.getenv("AWS_TEXTRACT_S3_BUCKET")
    self.client: Any = None
    self.s3_client: Any = None
    self.poll_interval_seconds = 2
    self.max_poll_attempts = 150

  def _create_session(self) -> Session:
    session_kwargs: dict[str, str] = {"region_name": self.region_name}
    if self.aws_access_key_id and self.aws_secret_access_key:
      session_kwargs["aws_access_key_id"] = self.aws_access_key_id
      session_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
      if self.aws_session_token:
        session_kwargs["aws_session_token"] = self.aws_session_token
    base_session = boto3.Session(**session_kwargs)
    if not self.role_arn:
      return base_session
    sts_client = base_session.client("sts", region_name=self.region_name)
    assume_kwargs = {
      "RoleArn": self.role_arn,
      "RoleSessionName": self.role_session_name,
    }
    if self.role_external_id:
      assume_kwargs["ExternalId"] = self.role_external_id
    response = sts_client.assume_role(**assume_kwargs)
    credentials = response["Credentials"]
    return boto3.Session(
      aws_access_key_id=credentials["AccessKeyId"],
      aws_secret_access_key=credentials["SecretAccessKey"],
      aws_session_token=credentials["SessionToken"],
      region_name=self.region_name,
    )

  def _ensure_clients(self) -> None:
    if self.client is not None and self.s3_client is not None:
      return
    session = self._create_session()
    self.client = session.client("textract", region_name=self.region_name)
    self.s3_client = session.client("s3", region_name=self.region_name)

  async def start_document_detection(self, bucket: str, object_key: str) -> str:
    try:
      self._ensure_clients()
      response = await asyncio.to_thread(
        self.client.start_document_text_detection,
        DocumentLocation={
          "S3Object": {
            "Bucket": bucket,
            "Name": object_key,
          }
        },
      )
      return response["JobId"]
    except ClientError as error:
      error_code = error.response.get("Error", {}).get("Code")
      if error_code == "UnsupportedDocumentException":
        raise ValueError(f"Unsupported document format: {error}") from error
      raise RuntimeError(f"Failed to start Textract job: {error}") from error

  async def poll_job_completion(self, job_id: str) -> bool:
    for attempt in range(self.max_poll_attempts):
      try:
        self._ensure_clients()
        response = await asyncio.to_thread(
          self.client.get_document_text_detection,
          JobId=job_id,
        )
        status = response["JobStatus"]
        if status == "SUCCEEDED":
          return True
        if status == "FAILED":
          raise RuntimeError(
            "Textract job failed: "
            f"{response.get('StatusMessage', 'Unknown error')}"
          )
        if status in ["IN_PROGRESS", "PARTIAL_SUCCESS"]:
          await asyncio.sleep(self.poll_interval_seconds)
          continue
        raise RuntimeError(f"Unexpected job status: {status}")
      except (ClientError, BotoCoreError) as error:
        if attempt == self.max_poll_attempts - 1:
          raise RuntimeError(
            "Polling failed after "
            f"{self.max_poll_attempts} attempts: {error}"
          ) from error
        await asyncio.sleep(self.poll_interval_seconds)
    raise RuntimeError(
      "Textract job timed out after "
      f"{self.max_poll_attempts * self.poll_interval_seconds} seconds"
    )

  async def extract_text(self, document_bytes: bytes) -> dict[str, Any]:
    return await self.extract_text_with_filename(document_bytes, None)

  async def extract_text_with_filename(
    self,
    document_bytes: bytes,
    filename: str | None,
  ) -> dict[str, Any]:
    extension = os.path.splitext(filename or "")[1].lower()
    try:
      self._ensure_clients()
      response = await asyncio.to_thread(
        self.client.detect_document_text,
        Document={"Bytes": document_bytes},
      )
      return response
    except ValueError:
      raise
    except (NoCredentialsError, PartialCredentialsError) as error:
      raise PermissionError("Invalid or missing AWS credentials") from error
    except ClientError as error:
      error_code = error.response.get("Error", {}).get("Code")
      if error_code == "UnsupportedDocumentException":
        if extension == ".pdf" and self.upload_bucket:
          return await self._extract_pdf_via_s3(document_bytes)
        if extension == ".pdf":
          raise ValueError(
            "PDF is not supported through DetectDocumentText bytes input. "
            "Set AWS_TEXTRACT_S3_BUCKET to enable automatic S3 fallback "
            "with StartDocumentTextDetection."
          ) from error
        raise ValueError(f"Unsupported document format: {error}") from error
      if error_code in {
        "AccessDenied",
        "AccessDeniedException",
        "UnrecognizedClientException",
      }:
        raise PermissionError("Invalid or missing AWS credentials") from error
      raise RuntimeError(f"Textract request failed: {error}") from error
    except BotoCoreError as error:
      raise RuntimeError(f"Textract request failed: {error}") from error

  async def _extract_pdf_via_s3(self, document_bytes: bytes) -> dict[str, Any]:
    if not self.upload_bucket:
      raise ValueError(
        "PDF could not be processed with DetectDocumentText. "
        "Set AWS_TEXTRACT_S3_BUCKET to enable StartDocumentTextDetection fallback."
      )
    object_key = f"textract-uploads/{uuid.uuid4()}.pdf"
    try:
      self._ensure_clients()
      await asyncio.to_thread(
        self.s3_client.put_object,
        Bucket=self.upload_bucket,
        Key=object_key,
        Body=document_bytes,
        ContentType="application/pdf",
      )
      job_id = await self.start_document_detection(self.upload_bucket, object_key)
      await self.poll_job_completion(job_id)
      blocks = []
      next_token = None
      while True:
        params = {"JobId": job_id}
        if next_token:
          params["NextToken"] = next_token
        page_response = await asyncio.to_thread(
          self.client.get_document_text_detection,
          **params,
        )
        blocks.extend(page_response.get("Blocks", []))
        next_token = page_response.get("NextToken")
        if not next_token:
          break
      return {"Blocks": blocks}
    except (NoCredentialsError, PartialCredentialsError) as error:
      raise PermissionError("Invalid or missing AWS credentials") from error
    except ClientError as error:
      error_code = error.response.get("Error", {}).get("Code")
      if error_code == "UnsupportedDocumentException":
        raise ValueError(f"Unsupported document format: {error}") from error
      if error_code in {
        "AccessDenied",
        "AccessDeniedException",
        "UnrecognizedClientException",
      }:
        raise PermissionError(
          "Access denied for S3/Textract operations. "
          "Ensure the active IAM principal has s3:PutObject, s3:GetObject, "
          "s3:DeleteObject on the configured bucket and Textract permissions."
        ) from error
      raise RuntimeError(f"Textract request failed: {error}") from error
    except BotoCoreError as error:
      raise RuntimeError(f"Textract request failed: {error}") from error
    finally:
      if self.upload_bucket:
        try:
          await asyncio.to_thread(
            self.s3_client.delete_object,
            Bucket=self.upload_bucket,
            Key=object_key,
          )
        except Exception:
          pass
