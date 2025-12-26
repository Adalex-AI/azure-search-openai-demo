import argparse
import logging
import os
import re
from pathlib import Path
from typing import Any

from azure.identity import AzureDeveloperCliCredential
from dotenv_azd import load_azd_env
from evaltools.eval.evaluate import run_evaluate_from_config
from evaltools.eval.evaluate_metrics import register_metric
from evaltools.eval.evaluate_metrics.base_metric import BaseMetric
from rich.logging import RichHandler

logger = logging.getLogger("ragapp")

# Regex pattern to match citations of the forms:
# [Document Name.pdf#page=7]
# [Document Name.pdf#page=4(figure4_1.png)]
# and supports multiple document extensions such as:
#  pdf, html/htm, doc/docx, ppt/pptx, xls/xlsx, csv, txt, json,
#  images: jpg/jpeg, png, bmp (listed as BPM in doc), tiff/tif, heif/heiff
# Optional components:
#   #page=\d+           -> page anchor (primarily for paged docs like PDFs)
#   ( ... )              -> figure/image or sub-resource reference (e.g., (figure4_1.png))
# Explanation of pattern components:
# \[                              - Opening bracket
# [^\]]+?\.                       - Non-greedy match of any chars up to a dot before extension
# (?:pdf|docx?|pptx?|xlsx?|csv|txt|json)
#                                  - Allowed primary file extensions
# (?:#page=\d+)?                  - Optional page reference
# (?:\([^()\]]+\))?             - Optional parenthetical (figure/image reference)
# \]                              - Closing bracket
CITATION_REGEX = re.compile(
    r"\[[^\]]+?\.(?:pdf|html?|docx?|pptx?|xlsx?|csv|txt|json|jpe?g|png|bmp|tiff?|heiff?|heif)(?:#page=\d+)?(?:\([^()\]]+\))?\]",
    re.IGNORECASE,
)


class AnyCitationMetric(BaseMetric):
    METRIC_NAME = "any_citation"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def any_citation(*, response, **kwargs):
            if response is None:
                logger.warning("Received response of None, can't compute any_citation metric. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            return {cls.METRIC_NAME: bool(CITATION_REGEX.search(response))}

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
            # Extract full citation tokens from ground truth and response
            truth_citations = set(CITATION_REGEX.findall(ground_truth or ""))
            response_citations = set(CITATION_REGEX.findall(response or ""))
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


# =============================================================================
# LEGAL DOMAIN METRICS (Custom - merge-safe)
# These metrics evaluate legal-specific quality aspects of RAG responses
# =============================================================================

# Regex patterns for legal references
# CPR Rule pattern: matches "CPR Part X" or "CPR X.Y" or "CPR Rule X.Y"
CPR_RULE_REGEX = re.compile(
    r"CPR\s+(?:Part\s+)?(\d+)(?:\.(\d+))?(?:\((\d+)\))?",
    re.IGNORECASE,
)

# Practice Direction pattern: matches "PD 51Z" or "Practice Direction 28A"
PRACTICE_DIRECTION_REGEX = re.compile(
    r"(?:Practice\s+Direction|PD)\s+(\d+[A-Z]?)",
    re.IGNORECASE,
)

# Court Guide pattern: matches "Chancery Guide" or "Queen's Bench Guide"
COURT_GUIDE_REGEX = re.compile(
    r"((?:Chancery|Queen'?s?\s+Bench|King'?s?\s+Bench|Commercial\s+Court|Admiralty|Technology\s+and\s+Construction)\s+Guide)",
    re.IGNORECASE,
)

# Statute pattern: matches legislation references like "Section 5 of the..."
STATUTE_REGEX = re.compile(
    r"(?:Section|s\.?)\s*(\d+)(?:\((\d+)\))?\s+(?:of\s+(?:the\s+)?)?([\w\s]+(?:Act|Regulations?|Rules?|Order)\s+\d{4})",
    re.IGNORECASE,
)

# Case citation pattern: matches "[2023] EWHC 123" or "[2024] UKSC 45" or "[2022] EWCA Civ 789"
CASE_CITATION_REGEX = re.compile(
    r"\[\d{4}\]\s+(EWHC|EWCA|UKSC|UKPC|UKHL)(?:\s+(?:Civ|Crim))?\s+\d+(?:\s+\([A-Za-z]+\))?",
    re.IGNORECASE,
)


class StatuteCitationAccuracyMetric(BaseMetric):
    """
    Measures the accuracy of statute/rule citations in legal RAG responses.
    
    Evaluates whether the response correctly cites:
    - CPR Rules (e.g., "CPR Part 36", "CPR 3.4")
    - Practice Directions (e.g., "PD 51Z", "Practice Direction 28A")  
    - Statutes (e.g., "Section 5 of the Limitation Act 1980")
    
    Returns the percentage of ground truth statute citations that appear in the response.
    """
    METRIC_NAME = "statute_citation_accuracy"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def statute_citation_accuracy(*, response, ground_truth, **kwargs) -> dict[str, Any]:
            if response is None:
                logger.warning("Received response of None, can't compute statute_citation_accuracy. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            # Extract all legal references from ground truth and response
            truth_refs = cls._extract_legal_references(ground_truth or "")
            response_refs = cls._extract_legal_references(response or "")
            
            if not truth_refs:
                # No statute citations expected in ground truth
                return {cls.METRIC_NAME: 1.0 if not response_refs else 0.5}
            
            # Calculate overlap
            matched = truth_refs.intersection(response_refs)
            accuracy = len(matched) / len(truth_refs)
            
            return {cls.METRIC_NAME: accuracy}
        
        return statute_citation_accuracy

    @classmethod
    def _extract_legal_references(cls, text: str) -> set[str]:
        """Extract normalized legal references from text."""
        refs = set()
        
        # Extract CPR rules
        for match in CPR_RULE_REGEX.finditer(text):
            part = match.group(1)
            rule = match.group(2) or ""
            subrule = match.group(3) or ""
            normalized = f"CPR_{part}"
            if rule:
                normalized += f".{rule}"
            if subrule:
                normalized += f"({subrule})"
            refs.add(normalized.upper())
        
        # Extract Practice Directions
        for match in PRACTICE_DIRECTION_REGEX.finditer(text):
            refs.add(f"PD_{match.group(1).upper()}")
        
        # Extract statutes
        for match in STATUTE_REGEX.finditer(text):
            section = match.group(1)
            subsection = match.group(2) or ""
            act_name = match.group(3).strip()
            # Normalize act name
            normalized_act = re.sub(r'\s+', '_', act_name.upper())
            normalized = f"S{section}"
            if subsection:
                normalized += f"({subsection})"
            normalized += f"_{normalized_act}"
            refs.add(normalized)
        
        return refs

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "mean_accuracy": round(df[cls.METRIC_NAME].mean(), 2) if len(df) > 0 else 0,
            "perfect_matches": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "total_evaluated": len(df),
        }


class CaseLawCitationMetric(BaseMetric):
    """
    Measures the presence and accuracy of case law citations in legal responses.
    
    Evaluates citations like:
    - [2023] EWHC 123 (Ch)
    - [2024] UKSC 45
    - [2022] EWCA Civ 789
    
    Returns 1.0 if all ground truth case citations are matched, 0.0 if none.
    """
    METRIC_NAME = "case_law_citation_accuracy"

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def case_law_citation_accuracy(*, response, ground_truth, **kwargs) -> dict[str, Any]:
            if response is None:
                logger.warning("Received response of None, can't compute case_law_citation_accuracy. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            # Extract case citations
            truth_cases = set(CASE_CITATION_REGEX.findall(ground_truth or ""))
            response_cases = set(CASE_CITATION_REGEX.findall(response or ""))
            
            if not truth_cases:
                # No case citations expected
                return {cls.METRIC_NAME: 1.0}
            
            # Normalize and compare
            truth_normalized = {c.upper() for c in truth_cases}
            response_normalized = {c.upper() for c in response_cases}
            
            matched = truth_normalized.intersection(response_normalized)
            accuracy = len(matched) / len(truth_normalized)
            
            return {cls.METRIC_NAME: accuracy}
        
        return case_law_citation_accuracy

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "mean_accuracy": round(df[cls.METRIC_NAME].mean(), 2) if len(df) > 0 else 0,
            "perfect_matches": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "total_evaluated": len(df),
        }


class LegalTerminologyMetric(BaseMetric):
    """
    Measures whether responses use correct legal terminology.
    
    Checks for proper use of key legal terms that should appear when
    discussing specific legal concepts (e.g., "claimant" vs "plaintiff",
    "disclosure" vs "discovery" in UK civil procedure).
    
    This is a presence-based metric that checks if key terms from
    ground truth appear in the response.
    """
    METRIC_NAME = "legal_terminology_accuracy"
    
    # Key legal terms to track (UK civil procedure focus)
    LEGAL_TERMS = {
        # Parties
        "claimant", "defendant", "respondent", "appellant", "applicant",
        # Procedures  
        "disclosure", "witness statement", "skeleton argument", "costs budget",
        "pre-action protocol", "particulars of claim", "defence", "reply",
        # Time/Deadlines
        "limitation period", "time limit", "extension of time",
        # Costs
        "costs order", "summary assessment", "detailed assessment",
        "qualified one-way costs shifting", "qocs", "fixed costs",
        # Judgments
        "summary judgment", "default judgment", "consent order", "tomlin order",
        # Tracks
        "small claims track", "fast track", "multi-track", "intermediate track",
    }

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def legal_terminology_accuracy(*, response, ground_truth, **kwargs) -> dict[str, Any]:
            if response is None:
                logger.warning("Received response of None, can't compute legal_terminology_accuracy. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            response_lower = response.lower()
            ground_truth_lower = (ground_truth or "").lower()
            
            # Find legal terms present in ground truth
            truth_terms = {term for term in cls.LEGAL_TERMS if term in ground_truth_lower}
            
            if not truth_terms:
                # No specific legal terms in ground truth
                return {cls.METRIC_NAME: 1.0}
            
            # Check which terms appear in response
            matched_terms = {term for term in truth_terms if term in response_lower}
            accuracy = len(matched_terms) / len(truth_terms)
            
            return {cls.METRIC_NAME: accuracy}
        
        return legal_terminology_accuracy

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "mean_accuracy": round(df[cls.METRIC_NAME].mean(), 2) if len(df) > 0 else 0,
            "perfect_matches": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "total_evaluated": len(df),
        }


class CitationFormatComplianceMetric(BaseMetric):
    """
    Measures compliance with legal citation format rules.
    
    For legal RAG, citations should follow the format [1][2][3] with
    single numbers in brackets, NOT comma-separated like [1, 2, 3].
    
    Returns 1.0 if all citations are properly formatted, 0.0 if malformed.
    """
    METRIC_NAME = "citation_format_compliance"
    
    # Proper format: [1] or [2] etc.
    PROPER_CITATION_REGEX = re.compile(r"\[(\d+)\]")
    
    # Malformed formats to detect
    MALFORMED_PATTERNS = [
        re.compile(r"\[\d+,\s*\d+"),  # [1, 2] or [1,2]
        re.compile(r"\d+,\s*\d+,"),   # 1, 2, 3 without brackets
        re.compile(r"\[\[\d+\]\]"),   # [[1]] double brackets
    ]

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def citation_format_compliance(*, response, **kwargs) -> dict[str, Any]:
            if response is None:
                logger.warning("Received response of None, can't compute citation_format_compliance. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            # Check for malformed patterns
            has_malformed = any(pattern.search(response) for pattern in cls.MALFORMED_PATTERNS)
            
            # Check for proper citations
            proper_citations = cls.PROPER_CITATION_REGEX.findall(response)
            has_proper = len(proper_citations) > 0
            
            if has_malformed:
                return {cls.METRIC_NAME: 0.0}
            elif has_proper:
                return {cls.METRIC_NAME: 1.0}
            else:
                # No citations at all - neutral
                return {cls.METRIC_NAME: 0.5}
        
        return citation_format_compliance

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "compliant_rate": round(df[cls.METRIC_NAME].mean(), 2) if len(df) > 0 else 0,
            "fully_compliant": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "malformed": int((df[cls.METRIC_NAME] == 0.0).sum()),
            "total_evaluated": len(df),
        }


class PrecedentMatchingMetric(BaseMetric):
    """
    Evaluates whether the response correctly matches legal precedents 
    and authorities mentioned in the ground truth.
    
    This metric checks for:
    1. Document source matching (e.g., same CPR part, same Practice Direction)
    2. Correct cross-referencing of related rules
    3. Proper hierarchical citation (e.g., CPR before PD)
    
    Uses the document citations [filename.pdf#page=X] to verify precedent matching.
    """
    METRIC_NAME = "precedent_matching"
    
    # Pattern to extract document names from citations
    DOC_NAME_REGEX = re.compile(r"\[([^\]#]+?)(?:#page=\d+)?(?:\([^)]+\))?\]")

    @classmethod
    def evaluator_fn(cls, **kwargs):
        def precedent_matching(*, response, ground_truth, **kwargs) -> dict[str, Any]:
            if response is None:
                logger.warning("Received response of None, can't compute precedent_matching. Setting to -1.")
                return {cls.METRIC_NAME: -1}
            
            # Extract document references from both
            truth_docs = set(cls.DOC_NAME_REGEX.findall(ground_truth or ""))
            response_docs = set(cls.DOC_NAME_REGEX.findall(response or ""))
            
            if not truth_docs:
                return {cls.METRIC_NAME: 1.0}
            
            # Normalize document names (lowercase, remove extensions)
            def normalize_doc(doc: str) -> str:
                return re.sub(r'\.(pdf|docx?|html?)$', '', doc.strip().lower())
            
            truth_normalized = {normalize_doc(d) for d in truth_docs}
            response_normalized = {normalize_doc(d) for d in response_docs}
            
            matched = truth_normalized.intersection(response_normalized)
            accuracy = len(matched) / len(truth_normalized)
            
            return {cls.METRIC_NAME: accuracy}
        
        return precedent_matching

    @classmethod
    def get_aggregate_stats(cls, df):
        df = df[df[cls.METRIC_NAME] != -1]
        return {
            "mean_accuracy": round(df[cls.METRIC_NAME].mean(), 2) if len(df) > 0 else 0,
            "perfect_matches": int((df[cls.METRIC_NAME] == 1.0).sum()),
            "partial_matches": int(((df[cls.METRIC_NAME] > 0) & (df[cls.METRIC_NAME] < 1.0)).sum()),
            "no_matches": int((df[cls.METRIC_NAME] == 0.0).sum()),
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
        logger.info("Setting up Azure credential using AzureDeveloperCliCredential with tenant_id %s", AZURE_TENANT_ID)
        azure_credential = AzureDeveloperCliCredential(tenant_id=AZURE_TENANT_ID, process_timeout=60)
    else:
        logger.info("Setting up Azure credential using AzureDeveloperCliCredential for home tenant")
        azure_credential = AzureDeveloperCliCredential(process_timeout=60)
    return azure_credential


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
    )
    logger.setLevel(logging.INFO)
    logging.getLogger("evaltools").setLevel(logging.INFO)
    load_azd_env()

    parser = argparse.ArgumentParser(description="Run evaluation with OpenAI configuration.")
    parser.add_argument("--targeturl", type=str, help="Specify the target URL.")
    parser.add_argument("--resultsdir", type=Path, help="Specify the results directory.")
    parser.add_argument("--numquestions", type=int, help="Specify the number of questions.")
    parser.add_argument("--config", type=str, default="evaluate_config.json", help="Specify the config file.")
    parser.add_argument("--groundtruth", type=str, help="Specify the ground truth file (overrides config).")

    args = parser.parse_args()

    openai_config = get_openai_config()

    # Register standard metrics
    register_metric(CitationsMatchedMetric)
    register_metric(AnyCitationMetric)

    # Register legal domain metrics (Custom - merge-safe)
    register_metric(StatuteCitationAccuracyMetric)
    register_metric(CaseLawCitationMetric)
    register_metric(LegalTerminologyMetric)
    register_metric(CitationFormatComplianceMetric)
    register_metric(PrecedentMatchingMetric)

    run_evaluate_from_config(
        working_dir=Path(__file__).parent,
        config_path=args.config,
        num_questions=args.numquestions,
        target_url=args.targeturl,
        results_dir=args.resultsdir,
        openai_config=openai_config,
        model=os.environ["AZURE_OPENAI_EVAL_MODEL"],
        azure_credential=get_azure_credential(),
    )
