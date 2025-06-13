#!/bin/bash

# API Base URL
BASE_URL="http://127.0.0.1:8000/invoke"

# Define the retriever endpoint paths (without the base URL and /invoke/)
ENDPOINTS=(
    "naive_retriever"
    "bm25_retriever"
    "contextual_compression_retriever"
    "multi_query_retriever"
    "ensemble_retriever"
    "semantic_retriever"
)

# Define the questions
QUESTIONS=(
    "Did people generally like John Wick?"
    "Do any reviews have a rating of 10? If so - can I have the URLs to those reviews?"
    "What happened in John Wick?"
)

# Create logs directory if it doesn't exist
LOGS_DIR="logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo "Creating directory: ${LOGS_DIR}"
    mkdir -p "$LOGS_DIR"
fi

# Create a timestamped log file in the logs directory
LOG_FILE="${LOGS_DIR}/api_test_results_$(date +%Y%m%d_%H%M%S).log"

echo "Starting API endpoint tests. Results will be logged to: ${LOG_FILE}"

# Function to make a curl request and log it
call_api() {
    local endpoint_name=$1
    local question_text=$2
    local full_url="${BASE_URL}/${endpoint_name}"

    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "Testing Endpoint: ${full_url}" | tee -a "${LOG_FILE}"
    echo "Question: ${question_text}" | tee -a "${LOG_FILE}"
    echo "Timestamp: $(date)" | tee -a "${LOG_FILE}"
    echo "Curl command:"
    echo "curl -s -X POST \"${full_url}\" -H \"Content-Type: application/json\" -d '{\"question\":\"${question_text}\"}'" | tee -a "${LOG_FILE}"
    echo "Response:" | tee -a "${LOG_FILE}"
    
    # Make the curl request. -s for silent, show error if any, write http code to know success
    HTTP_RESPONSE=$(curl -s -w "\nHTTP_STATUS_CODE:%{http_code}" -X POST "${full_url}" \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"${question_text//\"/\\\"}\"}")
    
    # Separate the body and the status code
    HTTP_BODY=$(echo "${HTTP_RESPONSE}" | sed '$d') # Get all but last line
    HTTP_STATUS_CODE=$(echo "${HTTP_RESPONSE}" | tail -n1 | cut -d: -f2) # Get last line, extract code

    echo "Status Code: ${HTTP_STATUS_CODE}" | tee -a "${LOG_FILE}"
    if [[ "${HTTP_STATUS_CODE}" -eq 200 ]]; then
        echo "${HTTP_BODY}" | jq '.' 2>/dev/null || echo "${HTTP_BODY}" # Try to pretty print if jq is available, otherwise raw
        echo "${HTTP_BODY}" >> "${LOG_FILE}" # Log raw body
    else
        echo "Error or non-200 response:"
        echo "${HTTP_BODY}"
        echo "${HTTP_BODY}" >> "${LOG_FILE}" # Log raw body
    fi
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "" | tee -a "${LOG_FILE}"
}

# Iterate over each endpoint and each question
for endpoint in "${ENDPOINTS[@]}"; do
    for question in "${QUESTIONS[@]}"; do
        call_api "${endpoint}" "${question}"
        # Optional: Add a small delay between requests if needed
        sleep 10
    done
done

echo "API endpoint tests completed. Full results logged to: ${LOG_FILE}" 