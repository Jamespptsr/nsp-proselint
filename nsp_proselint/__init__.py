"""
nsp-proselint: Formulaic prose detection and replacement for LLM outputs.

Detects cliche patterns in LLM-generated text and replaces them with
semantically equivalent synonyms, preserving sentence structure and context.

Designed as a shared library for the NSP ecosystem:
- nsp-roleplay: post-generation filter
- nsp-analysis: manuscript cliche audit + AI continuation quality
- nsp-edu: writing quality feedback
"""

__version__ = "0.1.0"

from .linter import ProseLinter, LintHit, Diff
from .loader import DictionaryLoader, Dictionary, PatternEntry, TestCase

__all__ = [
    "ProseLinter",
    "LintHit",
    "Diff",
    "DictionaryLoader",
    "Dictionary",
    "PatternEntry",
    "TestCase",
]
