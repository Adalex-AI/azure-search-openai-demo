#!/bin/bash
# Master diagnostic script - runs all tests and generates report

set -e

echo "======================================================================"
echo "BACKEND HANG MASTER DIAGNOSTIC"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Test Azure resource connectivity"
echo "  2. Check deployment status"
echo "  3. Apply diagnostic logging"
echo "  4. Restart backend with logging"
echo "  5. Test endpoint"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "======================================================================" 
echo "STEP 1: Azure Resource Connectivity Test"
echo "======================================================================"
cd "$(dirname "$0")/.."
source .venv/bin/activate
python scripts/test_azure_connectivity.py
echo ""

echo "======================================================================"
echo "STEP 2: Azure Deployment Status Check"
echo "======================================================================"
if [ -f scripts/check_azure_deployment.sh ]; then
    chmod +x scripts/check_azure_deployment.sh
    ./scripts/check_azure_deployment.sh
else
    echo "⚠ Skipped: check_azure_deployment.sh not found"
fi
echo ""

echo "======================================================================"
echo "STEP 3: Apply Diagnostic Logging (if not already applied)"
echo "======================================================================"
python scripts/add_diagnostic_logging.py
echo ""

echo "======================================================================"
echo "STEP 4: Restart Backend"
echo "======================================================================"
echo "Killing existing backend..."
kill $(lsof -ti:50505) 2>/dev/null || echo "No process on port 50505"
sleep 2

echo "Starting backend with diagnostic logging..."
source .azure/cpr-rag/.env
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
./.venv/bin/python -m quart --app app/backend/main:app run --port 50505 --host localhost --reload &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
sleep 5
echo ""

echo "======================================================================"
echo "STEP 5: Test Chat Endpoint"
echo "======================================================================"
echo "Sending test request..."
echo "Request: What is CPR 31?"
echo ""

# Send request with 20-second timeout and capture output
timeout 20 curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"What is CPR 31?","role":"user"}],"context":{"overrides":{}}}' \
  2>&1 || echo "Request timed out or failed"

echo ""
echo ""
echo "======================================================================"
echo "DIAGNOSTIC RESULTS"
echo "======================================================================"
echo ""
echo "Check backend terminal for 🔍 DIAGNOSTIC log messages"
echo "Last diagnostic message before hang indicates the failure point"
echo ""
echo "Common patterns:"
echo "  - Hangs after 'STEP 1 - Calling OpenAI' → Query rewrite API issue"
echo "  - Hangs after 'STEP 2 - Calling Azure Search' → Search API issue"
echo "  - Hangs after 'STEP 3 - Creating final chat completion' → Answer generation API issue"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "View logs: fg  (then Ctrl+C to stop)"
echo ""
echo "For detailed diagnosis, see:"
echo "  - BACKEND_HANG_DIAGNOSIS.md"
echo "  - EVALUATION_STATUS.md"
echo ""
