#!/bin/bash

##############################################################################
# Legal Document Scraper Pipeline
#
# Complete pipeline for scraping, validating, and uploading legal documents
# to Azure AI Search.
#
# Usage:
#   ./run_pipeline.sh [options]
#
# Options:
#   --help              Show this help message
#   --scrape            Run scraper only
#   --validate          Run validation only
#   --upload            Run upload only
#   --dry-run           Show what would be uploaded without uploading
#   --staging           Upload to staging index instead of production
#   --skip-validation   Skip validation step
#   --skip-approval     Skip approval prompt
#
# Examples:
#   ./run_pipeline.sh                    # Full pipeline (scrape → validate → upload)
#   ./run_pipeline.sh --dry-run          # Full pipeline but no actual upload
#   ./run_pipeline.sh --staging          # Upload to staging index
#   ./run_pipeline.sh --validate --input Upload  # Just validate existing data
#
##############################################################################

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data/legal-scraper"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Options
STEPS=("scrape" "validate" "upload")
DRY_RUN=false
STAGING=false
SKIP_VALIDATION=false
SKIP_APPROVAL=false
INPUT_DIR="Upload"
CUSTOM_STEPS=()

function print_help() {
    cat "$SCRIPT_DIR/run_pipeline.sh" | grep "^#" | tail -n +2 | sed 's/^# *//' | sed 's/^##*//'
}

function print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            print_help
            exit 0
            ;;
        --scrape)
            CUSTOM_STEPS=("scrape")
            shift
            ;;
        --validate)
            CUSTOM_STEPS=("validate")
            shift
            ;;
        --upload)
            CUSTOM_STEPS=("upload")
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --staging)
            STAGING=true
            shift
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --skip-approval)
            SKIP_APPROVAL=true
            shift
            ;;
        --input)
            INPUT_DIR="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Use custom steps if provided, otherwise use all
if [ ${#CUSTOM_STEPS[@]} -gt 0 ]; then
    STEPS=("${CUSTOM_STEPS[@]}")
fi

print_header "Legal Document Scraper Pipeline"
echo "Steps: ${STEPS[*]}"
echo "Input directory: $INPUT_DIR"
echo "Dry-run: $DRY_RUN"
echo "Staging: $STAGING"
echo ""

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    print_success "Virtual environment activated"
fi

# Step 1: Scrape
if [[ " ${STEPS[@]} " =~ " scrape " ]]; then
    print_header "Step 1: Scraping Civil Procedure Rules"
    print_info "This may take several minutes..."
    
    if python "$SCRIPT_DIR/scrape_cpr.py"; then
        print_success "Scraping completed"
    else
        print_error "Scraping failed"
        exit 1
    fi
fi

# Step 2: Validate
if [[ " ${STEPS[@]} " =~ " validate " ]]; then
    print_header "Step 2: Validating Documents"
    
    if [ "$SKIP_APPROVAL" = true ]; then
        APPROVE_FLAG="--no-approve"
    else
        APPROVE_FLAG=""
    fi
    
    if python "$SCRIPT_DIR/validate_and_review.py" --input "$INPUT_DIR" $APPROVE_FLAG; then
        print_success "Validation passed"
    else
        if [ "$SKIP_APPROVAL" = true ]; then
            print_warning "Validation step skipped approval (--skip-approval)"
        else
            print_error "Validation failed or was cancelled"
            exit 1
        fi
    fi
fi

# Step 3: Upload
if [[ " ${STEPS[@]} " =~ " upload " ]]; then
    print_header "Step 3: Uploading to Azure Search"
    
    UPLOAD_OPTS="--input $INPUT_DIR"
    [ "$DRY_RUN" = true ] && UPLOAD_OPTS="$UPLOAD_OPTS --dry-run"
    [ "$STAGING" = true ] && UPLOAD_OPTS="$UPLOAD_OPTS --staging"
    
    if python "$SCRIPT_DIR/upload_with_embeddings.py" $UPLOAD_OPTS; then
        print_success "Upload completed"
    else
        print_error "Upload failed"
        exit 1
    fi
fi

print_header "Pipeline Complete"
if [ "$DRY_RUN" = true ]; then
    print_warning "DRY-RUN MODE: No documents were actually uploaded"
    print_info "Run again without --dry-run to upload for real"
else
    print_success "Documents have been uploaded to Azure Search"
fi

print_info "For detailed results, see:"
print_info "  - Validation report: $DATA_DIR/validation-reports/"
print_info "  - Upload cache: $DATA_DIR/cache/"
