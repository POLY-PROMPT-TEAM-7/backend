#!/usr/bin/env bash

set -u

API_URL="${API_URL:-http://127.0.0.1:8000/api/documents/upload}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${SCRIPT_DIR}/test_files_gzip"

if [[ ! -d "${FILES_DIR}" ]]; then
  echo "Test files directory not found: ${FILES_DIR}" >&2
  exit 1
fi

echo "API URL: ${API_URL}"
echo "Using files from: ${FILES_DIR}"
echo

for file in "${FILES_DIR}"/*; do
  if [[ ! -f "${file}" ]]; then
    continue
  fi

  filename="$(basename "${file}")"
  response_file="$(mktemp)"

  echo "=== Testing existing file: ${filename} ==="
  http_code="$(curl -sS -o "${response_file}" -w "%{http_code}" -X POST "${API_URL}" -F "file=@${file}" )"
  curl_exit=$?

  if [[ ${curl_exit} -ne 0 ]]; then
    echo "curl failed with exit code ${curl_exit}"
  else
    echo "HTTP ${http_code}"
    cat "${response_file}"
    echo
  fi

  rm -f "${response_file}"
done

missing_file="${FILES_DIR}/__nonexistent_upload_test_file__.pdf.gz"
missing_response_file="$(mktemp)"

echo "=== Testing non-existent file path: ${missing_file} ==="
http_code="$(curl -sS -o "${missing_response_file}" -w "%{http_code}" -X POST "${API_URL}" -F "file=@${missing_file}" )"
curl_exit=$?

if [[ ${curl_exit} -ne 0 ]]; then
  echo "Expected behavior: curl failed for missing file (exit ${curl_exit})"
else
  echo "Unexpected behavior: curl succeeded"
  echo "HTTP ${http_code}"
  cat "${missing_response_file}"
  echo
fi

rm -f "${missing_response_file}"
