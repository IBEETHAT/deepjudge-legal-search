"""
DeepJudge Legal Search Client
A production-ready Python client for legal knowledge search and analysis
"""

__version__ = "1.0.0"
__author__ = "DeepJudge Team"

from .client import DeepJudgeClient
from .features import (
    GreyAreaAnalyzer,
    RegulatoryLoopholeAnalyzer,
    RiskAssessor,
    DefenseStrategyResearcher,
    ComplianceOptimizer
)

__all__ = [
    "DeepJudgeClient",
    "GreyAreaAnalyzer",
    "RegulatoryLoopholeAnalyzer",
    "RiskAssessor",
    "DefenseStrategyResearcher",
    "ComplianceOptimizer"
]
