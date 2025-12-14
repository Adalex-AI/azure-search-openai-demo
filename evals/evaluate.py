import argparse
import json
import logging
import os
import re
from pathlib import Path

from azure.identity import AzureCliCredential
from dotenv_azd import load_azd_env
from evaltools.eval.evaluate import run_evaluate_from_config
from evaltools.eval.evaluate_metrics import register_metric
from evaltools.eval.evaluate_metrics.base_metric import BaseMetric
from rich.logging import RichHandler

logger = logging.getLogger("ragapp")


class AnyCitationMetric(BaseMetric):
    METRIC_NAME = "any_citation"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def any_citation(*, response, **kwargs):
            if response is None:
                logger.warning("Received response of None, can't compute any_citation metric. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            # Updated to match new simple numeric citation format: [1], [2], [3]
            return {cls.METRIC_NAME: bool(re.search(r"\[\d+\]", response))}

        return any_citation

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "total": int(df[cls.METRIC_NAME].sum()),
            "rate": round(df[cls.METRIC_NAME].mean(), 2),
        }


class CitationsMatchedMetric(BaseMetric):
    METRIC_NAME = "citations_matched"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def citations_matched(*, response, ground_truth, **kwargs):
            if response is None:
                logger.warning("Received response of None, can't compute citation_match metric. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            # Updated to match new simple numeric citation format: [1], [2], [3]
            # Extract citation numbers from ground truth and response
            truth_citations = set(re.findall(r"\[(\d+)\]", ground_truth))
            response_citations = set(re.findall(r"\[(\d+)\]", response))
            
            # If no citations in ground truth, return perfect score
            if not truth_citations:
                return {cls.METRIC_NAME: 1.0}
            
            # Count the percentage of citations that are present in the response
            num_citations = len(truth_citations)
            num_matched_citations = len(truth_citations.intersection(response_citations))
            return {cls.METRIC_NAME: num_matched_citations / num_citations}

        return citations_matched

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "total": int(df[cls.METRIC_NAME].sum()),
            "rate": round(df[cls.METRIC_NAME].mean(), 2),
        }


class CitationFormatComplianceMetric(BaseMetric):
    """Validates that citations follow strict [N][M] format with no commas or other prohibited patterns"""
    METRIC_NAME = "citation_format_compliance"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def citation_format_compliance(*, response, **kwargs):
            if response is None:
                logger.warning("Received response of None, can't compute citation_format_compliance metric. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            # Check for PROHIBITED citation patterns from CITATION_FORMAT_FIXES.md
            prohibited_patterns = [
                r"\[\d+,\s*\d+\]",              # [1, 2] or [1, 2, 3]
                r"(?<!\[)\d+,\s*\d+(?:,\s*\d+)*\s*\[",  # 1, 2, [3] or 1, 2, 3[4]
                r"\[\d+\],\s*\[\d+\]",          # [1], [2] (should be [1][2])
                r"(?<!\[)\d+,\s*\d+(?![\]\d])", # 1, 2, 3 (naked comma-separated numbers)
            ]
            
            violations = []
            for pattern in prohibited_patterns:
                matches = re.findall(pattern, response)
                if matches:
                    violations.extend(matches)
            
            # Score: 1.0 if no violations, 0.0 if any violations found
            is_compliant = len(violations) == 0
            
            if not is_compliant:
                logger.warning(f"Citation format violations found: {violations}")
            
            return {cls.METRIC_NAME: 1.0 if is_compliant else 0.0}

        return citation_format_compliance

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "total_compliant": int(df[cls.METRIC_NAME].sum()),
            "compliance_rate": round(df[cls.METRIC_NAME].mean(), 2),
            "total_violations": int((1 - df[cls.METRIC_NAME]).sum()),
        }


class SubsectionExtractionMetric(BaseMetric):
    """Validates that subsection/paragraph numbers in responses match source documents"""
    METRIC_NAME = "subsection_extraction_accuracy"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def subsection_accuracy(*, response, context, **kwargs):
            if response is None:
                logger.warning("Received response of None, can't compute subsection_extraction_accuracy metric. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            # Patterns for legal subsections: 31.1, A4.1, PD 3E-1.1, Part 35, etc.
            subsection_patterns = [
                r'\bCPR\s+(?:Part\s+)?(\d+)\.(\d+)\b',  # CPR 31.1 or CPR Part 31.1
                r'\b(?:Part\s+)?(\d+)\.(\d+)\b',         # 31.1, Part 31.1
                r'\b([A-Z])(\d+)\.(\d+)\b',              # A4.1, D5.2
                r'\bPD\s+(\d+[A-Z]*)-(\d+)\.(\d+)\b',    # PD 3E-1.1
                r'\b([A-Z]\d+\.\d+)\b',                  # Generic letter+number format
            ]
            
            # Extract all subsection references from response
            mentioned_subsections = set()
            for pattern in subsection_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # Join tuple elements to form complete reference
                        subsection = '.'.join(str(m) for m in match if m)
                    else:
                        subsection = match
                    mentioned_subsections.add(subsection)
            
            # If no subsections mentioned, return perfect score (nothing to validate)
            if not mentioned_subsections:
                return {cls.METRIC_NAME: 1.0}
            
            # Get source documents from context
            try:
                sources = context.get('data_points', {}).get('text', [])
                if not sources:
                    logger.warning("No source documents in context for subsection validation")
                    return {cls.METRIC_NAME: -1}
                
                # Extract all subsections from source documents
                source_subsections = set()
                for source in sources:
                    content = source.get('content', '')
                    sourcepage = source.get('sourcepage', '')
                    
                    # Check both content and sourcepage for subsection numbers
                    for text in [content, sourcepage]:
                        for pattern in subsection_patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            for match in matches:
                                if isinstance(match, tuple):
                                    subsection = '.'.join(str(m) for m in match if m)
                                else:
                                    subsection = match
                                source_subsections.add(subsection)
                
                # Calculate accuracy: mentioned subsections that exist in sources
                if source_subsections:
                    correct = sum(1 for sub in mentioned_subsections 
                                 if any(sub in source_sub or source_sub in sub 
                                       for source_sub in source_subsections))
                    accuracy = correct / len(mentioned_subsections)
                else:
                    # No subsections found in sources, but mentioned in response = hallucination
                    accuracy = 0.0
                
                return {cls.METRIC_NAME: accuracy}
                
            except Exception as e:
                logger.error(f"Error in subsection extraction metric: {e}")
                return {cls.METRIC_NAME: -1}

        return subsection_accuracy

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "mean_accuracy": round(df[cls.METRIC_NAME].mean(), 2),
            "perfect_extractions": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "total_evaluated": len(df),
        }


class CategoryCoverageMetric(BaseMetric):
    """Validates that system retrieves from correct court categories based on query"""
    METRIC_NAME = "category_coverage"
    
    # Available categories in the legal knowledge base
    COURT_CATEGORIES = [
        "Civil Procedure Rules",
        "Commercial Court",
        "Circuit Commercial Court", 
        "King's Bench Division",
        "High Court",
        "County Court",
        "Chancery",
        "Patents Court",
        "Technology and Construction Court"
    ]
    
    # Court name variations for detection
    COURT_PATTERNS = {
        "Commercial Court": [r"\bcommercial\s+court\b"],
        "Circuit Commercial Court": [r"\bcircuit\s+commercial\s+court\b", r"\bCCC\b"],
        "King's Bench Division": [r"\bking'?s\s+bench\b", r"\bKBD\b", r"\bqueen'?s\s+bench\b", r"\bQBD\b"],
        "High Court": [r"\bhigh\s+court\b"],
        "County Court": [r"\bcounty\s+court\b"],
        "Chancery": [r"\bchancery\b"],
        "Patents Court": [r"\bpatents\s+court\b"],
        "Technology and Construction Court": [r"\btechnology\s+and\s+construction\s+court\b", r"\bTCC\b"],
    }

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def category_coverage(*, response, context, query, **kwargs):
            if response is None:
                logger.warning("Received response of None, can't compute category_coverage metric. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            try:
                # Parse context if it's a string
                if isinstance(context, str):
                    context = json.loads(context)
                
                # Detect if query mentions a specific court
                mentioned_court = None
                query_lower = query.lower()
                
                for court, patterns in cls.COURT_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, query_lower, re.IGNORECASE):
                            mentioned_court = court
                            break
                    if mentioned_court:
                        break
                
                # Get source categories from context
                sources = context.get('data_points', {}).get('text', [])
                if not sources:
                    logger.warning("No source documents in context for category validation")
                    return {cls.METRIC_NAME: -1}
                
                source_categories = [s.get('category', '') for s in sources]
                source_categories = [cat for cat in source_categories if cat]  # Remove empty
                
                if mentioned_court:
                    # Verify response cites from correct category
                    # Should include mentioned court OR CPR (which applies to all courts)
                    has_court_specific = any(mentioned_court in cat for cat in source_categories)
                    has_cpr_fallback = any("Civil Procedure Rules" in cat or "CPR" in cat 
                                           for cat in source_categories)
                    
                    is_correct = has_court_specific or has_cpr_fallback
                    
                    if not is_correct:
                        logger.warning(f"Query asked about '{mentioned_court}' but sources are from: {set(source_categories)}")
                    
                    return {cls.METRIC_NAME: 1.0 if is_correct else 0.0}
                else:
                    # No specific court mentioned - any category is acceptable
                    # But should have at least some categorized sources
                    return {cls.METRIC_NAME: 1.0 if source_categories else 0.5}
                    
            except Exception as e:
                logger.error(f"Error in category coverage metric: {e}")
                return {cls.METRIC_NAME: -1}

        return category_coverage

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "mean_coverage": round(df[cls.METRIC_NAME].mean(), 2),
            "perfect_coverage": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "total_evaluated": len(df),
        }


def get_openai_config():
    azure_endpoint = f"https://{os.getenv('AZURE_OPENAI_SERVICE')}.openai.azure.com"
    azure_deployment = os.environ["AZURE_OPENAI_EVAL_DEPLOYMENT"]
    openai_config = {"azure_endpoint": azure_endpoint, "azure_deployment": azure_deployment}
    # azure-ai-evaluate will call DefaultAzureCredential behind the scenes,
    # so we must be logged in to Azure CLI with the correct tenant
    return openai_config


def get_azure_credential():
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    if AZURE_TENANT_ID:
        logger.info("Setting up Azure credential using AzureCliCredential with tenant_id %s", AZURE_TENANT_ID)
        azure_credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)
    else:
        logger.info("Setting up Azure credential using AzureCliCredential for home tenant")
        azure_credential = AzureCliCredential()
    return azure_credential


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
    )
    logger.setLevel(logging.INFO)
    logging.getLogger("evaltools").setLevel(logging.INFO)
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".azure" / "cpr-rag" / ".env"
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(description="Run evaluation with OpenAI configuration.")
    parser.add_argument("--targeturl", type=str, help="Specify the target URL.")
    parser.add_argument("--resultsdir", type=Path, help="Specify the results directory.")
    parser.add_argument("--numquestions", type=int, help="Specify the number of questions.")

    args = parser.parse_args()

    openai_config = get_openai_config()

    # Register all custom metrics
    register_metric(AnyCitationMetric)
    register_metric(CitationsMatchedMetric)
    register_metric(CitationFormatComplianceMetric)
    register_metric(SubsectionExtractionMetric)
    register_metric(CategoryCoverageMetric)

    run_evaluate_from_config(
        working_dir=Path(__file__).parent,
        config_path="evaluate_config.json",
        num_questions=args.numquestions,
        target_url=args.targeturl,
        results_dir=args.resultsdir,
        openai_config=openai_config,
        model=os.environ["AZURE_OPENAI_EVAL_MODEL"],
        azure_credential=get_azure_credential(),
    )
