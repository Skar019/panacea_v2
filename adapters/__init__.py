from .base import ADAPTERS, Result, register
# Importing a file registers its source. To add a source: write the file, add it here.
from . import arxiv, github, semantic_scholar, openalex, pubmed, tavily, huggingface
