import asyncio
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class TextractClient:
    def __init__(self, region_name: Optional[str] = None):
        self.client = boto3.client("textract", region_name=region_name)
        self.poll_interval_seconds = 2
        self.max_poll_attempts = 150

    async def start_document_detection(self, document_bytes: bytes) -> str:
        try:
            response = await asyncio.to_thread(
                self.client.start_document_text_detection,
                Document={"Bytes": document_bytes},
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

    async def extract_text(self, document_bytes: bytes) -> dict:
        job_id = await self.start_document_detection(document_bytes)
        await self.poll_job_completion(job_id)
        response = await asyncio.to_thread(
            self.client.get_document_text_detection,
            JobId=job_id,
        )
        return response
