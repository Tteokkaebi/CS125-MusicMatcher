#indexer_searcher/tokenizer.py
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
import re
from InvertedIndex import FrequencyList

ps = PorterStemmer()


"""
This module handles text tokenization and frequency analysis for the indexer.

Key Features:
1. Converts raw HTML into normalized, stemmed tokens (unigrams).
2. Generates 2-grams and 3-grams from unigrams for better phrase and proximity matching.
3. Produces frequency lists for each token (normal, heading, title) for weighted tf calculation.
4. Designed to work with BeautifulSoup-parsed HTML.
5. N-grams are optional, but included here to improve search quality and recall.

Why n-grams:
- Single-word queries are often insufficient for capturing context.
- 2-grams and 3-grams help the searcher recognize phrases and multi-word terms.
- These tokens are indexed the same way as unigrams, but can later be used for phrase queries or better ranking.
"""

# ----------------------- Tokenization Helpers ----------------------
def tokenize(text: str) -> list[str]:
    """
    Splits text into lowercase alphanumeric tokens and stems them.
    Ignores tokens shorter than 3 characters.
    Returns a list of stemmed tokens (unigrams).
    """
    tokens = re.split(r'[^a-zA-Z0-9]+', text.lower())
    return [ps.stem(t) for t in tokens if len(t) > 2]


def generate_ngrams(tokens: list[str], n: int) -> list[str]:
    """
    Generate n-grams from a list of tokens.
    For example, n=2 generates 2-grams (pairs of consecutive tokens).
    Returns a list of n-gram strings joined with underscores.
    """
    if n < 2:
        return []
    return ['_'.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


# ----------------------- Token Frequency Extraction ----------------------
def get_token_frequencies(soup: BeautifulSoup) -> dict[str, FrequencyList]:
    """
    Returns a dictionary mapping token (or n-gram) -> FrequencyList for a document.

    Workflow:
    1. Extract text from <title>, <h1-h6>, and <p> tags.
    2. Tokenize text into stemmed unigrams.
    3. Generate 2-grams and 3-grams from unigrams.
    4. Update token_map with frequencies, weighted by section type:
       - normal text: weight=1
       - headings: weight=10
       - title: weight=5
    5. Each token/gram is stored in a FrequencyList with total count.

    This structure allows the indexer to compute weighted tf scores.
    """
    token_map: dict[str, FrequencyList] = {}

    # ----------------------- Title Tokens ----------------------
    if soup.title and soup.title.string:
        title_tokens = tokenize(soup.title.string)
        ngrams = title_tokens + generate_ngrams(title_tokens, 2) + generate_ngrams(title_tokens, 3)
        for token in ngrams:
            token_map.setdefault(token, FrequencyList()).title += 1
            token_map[token].total += 1

    # ----------------------- Heading Tokens ----------------------
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        header_tokens = tokenize(header.get_text(" ", strip=True))
        ngrams = header_tokens + generate_ngrams(header_tokens, 2) + generate_ngrams(header_tokens, 3)
        for token in ngrams:
            token_map.setdefault(token, FrequencyList()).heading += 1
            token_map[token].total += 1

    # ----------------------- Paragraph Tokens ----------------------
    for para in soup.find_all("p"):
        para_tokens = tokenize(para.get_text(" ", strip=True))
        ngrams = para_tokens + generate_ngrams(para_tokens, 2) + generate_ngrams(para_tokens, 3)
        for token in ngrams:
            token_map.setdefault(token, FrequencyList()).normal += 1
            token_map[token].total += 1

    return token_map
