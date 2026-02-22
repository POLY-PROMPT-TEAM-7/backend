To run tests run this command in the backend directory:
nix shell --command pytest tests/document_processor/test_upload_api.py -q

To test json outputs:
./run_curl_upload_tests.sh
