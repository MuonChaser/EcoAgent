"""
AES (Automatic Essay Scoring) Configuration
"""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# AES scoring system configuration
AES_CONFIG = {
    # Stopwords path
    "stopwords_path": str(PROJECT_ROOT / "data" / "stopwords_en.txt"),

    # Sentence embedding model
    # Options: paraphrase-multilingual-MiniLM-L12-v2, distiluse-base-multilingual-cased
    "sentence_model": "paraphrase-multilingual-MiniLM-L12-v2",

    # NLI model
    # Options: microsoft/deberta-v3-base, cross-encoder/nli-deberta-v3-base
    "nli_model": "cross-encoder/nli-deberta-v3-base",

    # Metric weights (sum to 1.0)
    "weights": {
        # NLP-based quantitative metrics (5)
        "citation_coverage": 0.15,      # Citation coverage
        "causal_relevance": 0.15,       # Causal relevance
        "support_strength": 0.20,       # Support strength
        "contradiction_penalty": 0.15,  # Contradiction penalty
        "evidence_sufficiency": 0.15,   # Evidence sufficiency
        # LLM-based qualitative metrics (3, extracted from LLM review)
        "endogeneity_quality": 0.07,    # Endogeneity treatment quality (good=1.0, average=0.5, poor=0.0)
        "methodology_rigor": 0.07,      # Methodology rigor (converted from model design score)
        "academic_standards": 0.06,     # Academic standards (converted from paper quality score)
    },

    # Evidence requirements by claim type (higher requirements for stricter scoring)
    "evidence_needs": {
        "background": 1,      # Background statements need 1 evidence
        "general": 2,         # General statements need 2 evidences
        "hypothesis": 5,      # Hypotheses need 5 evidences
        "conclusion": 5,      # Conclusions need 5 evidences
        "mechanism": 4,       # Mechanism analysis needs 4 evidences
    },

    # Citation coverage parameters
    "citation_coverage": {
        "min_evidences_per_claim": 4,  # Minimum evidence per claim to count as covered
        "use_weighted_coverage": True,  # Use weighted coverage (considering evidence count)
    },

    # Claim classification keywords
    "claim_keywords": {
        "hypothesis": ["hypothesis", "hypothesize", "H1", "H2", "H3", "proposition", "expect", "predict"],
        "conclusion": ["conclusion", "indicate", "demonstrate", "find", "show", "results show", "evidence suggests"],
        "mechanism": ["mechanism", "pathway", "mediation", "moderation", "channel", "transmission"],
        "background": ["background", "context", "policy", "institution", "history", "development"],
    },

    # Evidence extraction patterns
    "evidence_patterns": {
        # Citation patterns
        "citation": [
            r'[\(（]([^)）]*\d{4}[^)）]*)[\)）]',  # (Author, 2020)
            r'\\citep?\{[^}]+\}',                  # \citep{ref}
            r'[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)',  # Smith et al. (2020)
        ],
        # Data keywords
        "data_keywords": ["data", "sample", "observation", "firm", "average", "standard deviation", "mean", "median"],
        # Result keywords
        "result_keywords": ["coefficient", "significant", "p-value", "t-value", "R²", "regression", "estimate", "effect"],
    },

    # Similarity thresholds
    "thresholds": {
        "claim_evidence_similarity": 0.3,  # Claim-Evidence binding threshold
        "contradiction_threshold": 0.5,     # Contradiction detection threshold
        "support_threshold": 0.5,           # Support strength threshold
        "neutral_support_score": 0.6,       # Neutral label support score (0-1, recommend 0.5-0.7)
    },

    # Text processing parameters
    "text_processing": {
        "min_claim_length": 10,   # Minimum claim length
        "max_claim_length": 500,  # Maximum claim length
        "min_evidence_length": 5,  # Minimum evidence length
    },

    # Performance optimization parameters
    "performance": {
        "nli_batch_size": 32,              # NLI batch inference size
        "max_support_pairs": 999999,       # Max pairs for support strength (999999 = unlimited)
        "max_contradiction_pairs": 999999, # Max pairs for contradiction detection (999999 = unlimited)
        "max_evidences_per_claim": 999,    # Max evidences sampled per claim (999 = unlimited)
        "enable_nli": True,                # Whether to enable NLI computation (False uses defaults)
    },
}


def get_aes_config():
    """Get AES configuration"""
    return AES_CONFIG.copy()