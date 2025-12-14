#!/bin/bash
# Azure Deployment Status Checker
# Checks if Azure OpenAI deployment exists and has available quota

set -e

echo "======================================================================"
echo "AZURE DEPLOYMENT STATUS CHECKER"
echo "======================================================================"
echo ""

# Load environment
if [ -f .azure/cpr-rag/.env ]; then
    source .azure/cpr-rag/.env
    echo "✓ Environment loaded from .azure/cpr-rag/.env"
else
    echo "✗ Environment file not found: .azure/cpr-rag/.env"
    exit 1
fi

echo ""
echo "Configuration:"
echo "  Resource Group: ${AZURE_RESOURCE_GROUP:-N/A}"
echo "  OpenAI Service: ${AZURE_OPENAI_SERVICE:-N/A}"
echo "  Deployment: ${AZURE_OPENAI_CHATGPT_DEPLOYMENT:-N/A}"
echo "  Search Service: ${AZURE_SEARCH_SERVICE:-N/A}"
echo ""

# Check azd authentication
echo "----------------------------------------------------------------------"
echo "TEST 1: Azure Developer CLI Authentication"
echo "----------------------------------------------------------------------"
if command -v azd &> /dev/null; then
    if /usr/local/bin/azd auth login --check-status &> /dev/null; then
        ACCOUNT=$(/usr/local/bin/azd auth login --check-status 2>&1 | grep "Logged in" | cut -d' ' -f7-)
        echo "✓ Authenticated as: $ACCOUNT"
    else
        echo "✗ Not authenticated. Run: azd auth login --use-device-code"
        exit 1
    fi
else
    echo "✗ azd not found in PATH"
    exit 1
fi
echo ""

# Check Azure CLI (optional but helpful)
echo "----------------------------------------------------------------------"
echo "TEST 2: Azure CLI (optional)"
echo "----------------------------------------------------------------------"
if command -v az &> /dev/null; then
    if az account show &> /dev/null; then
        ACCOUNT=$(az account show --query user.name -o tsv)
        SUBSCRIPTION=$(az account show --query name -o tsv)
        echo "✓ Azure CLI authenticated"
        echo "  Account: $ACCOUNT"
        echo "  Subscription: $SUBSCRIPTION"
    else
        echo "⚠ Azure CLI not authenticated (optional)"
        echo "  Run: az login"
    fi
else
    echo "⚠ Azure CLI not installed (optional)"
    echo "  Install: brew install azure-cli"
fi
echo ""

# Check OpenAI deployment
echo "----------------------------------------------------------------------"
echo "TEST 3: Azure OpenAI Deployment Status"
echo "----------------------------------------------------------------------"
if [ -z "${AZURE_OPENAI_SERVICE}" ] || [ -z "${AZURE_RESOURCE_GROUP}" ]; then
    echo "⚠ SKIPPED: Missing AZURE_OPENAI_SERVICE or AZURE_RESOURCE_GROUP"
elif command -v az &> /dev/null && az account show &> /dev/null; then
    echo "Checking deployment: ${AZURE_OPENAI_CHATGPT_DEPLOYMENT}..."
    
    DEPLOYMENT_INFO=$(az cognitiveservices account deployment show \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --name "${AZURE_OPENAI_SERVICE}" \
        --deployment-name "${AZURE_OPENAI_CHATGPT_DEPLOYMENT}" \
        2>&1 || echo "ERROR")
    
    if [[ "$DEPLOYMENT_INFO" == *"ERROR"* ]] || [[ "$DEPLOYMENT_INFO" == *"not found"* ]]; then
        echo "✗ Deployment not found or inaccessible"
        echo "  This could explain the backend hang!"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check Azure Portal for deployment status"
        echo "  2. Verify deployment name matches .env configuration"
        echo "  3. Check if deployment is in 'Succeeded' provisioning state"
    else
        echo "✓ Deployment found"
        echo ""
        echo "$DEPLOYMENT_INFO" | jq -r '
            "Details:",
            "  Name: " + .name,
            "  Model: " + .properties.model.name,
            "  Version: " + .properties.model.version,
            "  Provisioning State: " + .properties.provisioningState,
            "  Capacity: " + (.sku.capacity | tostring)
        ' 2>/dev/null || echo "$DEPLOYMENT_INFO"
        
        PROVISIONING_STATE=$(echo "$DEPLOYMENT_INFO" | jq -r '.properties.provisioningState' 2>/dev/null || echo "Unknown")
        
        if [ "$PROVISIONING_STATE" != "Succeeded" ]; then
            echo ""
            echo "⚠ WARNING: Provisioning state is not 'Succeeded'"
            echo "  Current state: $PROVISIONING_STATE"
            echo "  This could cause backend to hang while waiting for deployment!"
        fi
    fi
else
    echo "⚠ SKIPPED: Azure CLI required for deployment check"
fi
echo ""

# Check Search service
echo "----------------------------------------------------------------------"
echo "TEST 4: Azure Search Service Status"
echo "----------------------------------------------------------------------"
if [ -z "${AZURE_SEARCH_SERVICE}" ] || [ -z "${AZURE_RESOURCE_GROUP}" ]; then
    echo "⚠ SKIPPED: Missing AZURE_SEARCH_SERVICE or AZURE_RESOURCE_GROUP"
elif command -v az &> /dev/null && az account show &> /dev/null; then
    echo "Checking search service: ${AZURE_SEARCH_SERVICE}..."
    
    SEARCH_INFO=$(az search service show \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --name "${AZURE_SEARCH_SERVICE}" \
        2>&1 || echo "ERROR")
    
    if [[ "$SEARCH_INFO" == *"ERROR"* ]] || [[ "$SEARCH_INFO" == *"not found"* ]]; then
        echo "✗ Search service not found or inaccessible"
    else
        echo "✓ Search service found"
        echo ""
        echo "$SEARCH_INFO" | jq -r '
            "Details:",
            "  Name: " + .name,
            "  Status: " + .status,
            "  Provisioning State: " + .provisioningState,
            "  SKU: " + .sku.name
        ' 2>/dev/null || echo "$SEARCH_INFO"
        
        STATUS=$(echo "$SEARCH_INFO" | jq -r '.status' 2>/dev/null || echo "Unknown")
        
        if [ "$STATUS" != "running" ]; then
            echo ""
            echo "⚠ WARNING: Search service status is not 'running'"
            echo "  Current status: $STATUS"
            echo "  This could cause backend search queries to hang!"
        fi
    fi
else
    echo "⚠ SKIPPED: Azure CLI required for search service check"
fi
echo ""

# Check resource quotas
echo "----------------------------------------------------------------------"
echo "TEST 5: OpenAI Quota and Rate Limits"
echo "----------------------------------------------------------------------"
if command -v az &> /dev/null && az account show &> /dev/null; then
    echo "Checking OpenAI service usage..."
    
    # Try to get usage (may not be available in all regions/SKUs)
    USAGE_INFO=$(az cognitiveservices account show \
        --resource-group "${AZURE_RESOURCE_GROUP}" \
        --name "${AZURE_OPENAI_SERVICE}" \
        --query "properties" \
        2>&1 || echo "ERROR")
    
    if [[ "$USAGE_INFO" != *"ERROR"* ]]; then
        echo "✓ Service properties retrieved"
        echo ""
        echo "Note: Detailed quota information requires Azure Monitor or direct API calls"
        echo "To check quota in Azure Portal:"
        echo "  1. Navigate to your OpenAI resource"
        echo "  2. Go to 'Quota' or 'Usage + quotas' blade"
        echo "  3. Check if deployment has available tokens-per-minute (TPM)"
    else
        echo "⚠ Could not retrieve usage information"
    fi
else
    echo "⚠ SKIPPED: Azure CLI required"
fi
echo ""

echo "======================================================================"
echo "SUMMARY"
echo "======================================================================"
echo ""
echo "Common causes of backend hang:"
echo "  1. ✗ Deployment in provisioning/failed state (not 'Succeeded')"
echo "  2. ✗ Search service not running"
echo "  3. ✗ Rate limit/quota exhausted (check Azure Portal)"
echo "  4. ✗ Network connectivity (firewall, VPN)"
echo "  5. ✗ Model not responding (Azure service issue)"
echo ""
echo "Next steps:"
echo "  1. Review any warnings/errors above"
echo "  2. Check Azure Portal for detailed quota/health status"
echo "  3. Run: python scripts/test_azure_connectivity.py"
echo "  4. Add diagnostic logging: python scripts/add_diagnostic_logging.py"
echo ""
