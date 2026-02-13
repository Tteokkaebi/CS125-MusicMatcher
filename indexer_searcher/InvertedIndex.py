#indexer_searcher/InvertedIndex.py
from dataclasses import dataclass
import math

@dataclass
class FrequencyList:
    normal: int = 0
    title: int = 0
    heading: int = 0
    total: int = 0

@dataclass
class DocumentInfo:
    id: int
    url: str
    total_tokens: int

class InvertedIndex():

    def __init__(self):

        # This is the main index that stores the token: [ID:TF]
        self.index = {}

        # This maps the docID to the DocumentInfo dataclass
        self.id_map = {}

        # This will keep track of the id of the document
        self.id_counter = 0

        self.current_doc_id = None
        self.current_url = None

    @staticmethod
    def compute_total_tokens(token_freqs: dict[str, FrequencyList]) -> int:
        """Static method that calculates the documents total tokesn using the frequency lists

        Args:
            token_freqs (dict[str, FrequencyList]): tokens and freq_lists of an entire document

        Returns:
            int: total number of tokens in the document
        """
        return sum(
            fl.total for fl in token_freqs.values()
        )

    
    def add_item(self, token : str, freq_list : FrequencyList) -> None:
        """Adds an item to the InvertedIndex. Maps the token:[ID, TF] into the main index, maps ID:DocumentInfo into the id_map

        Args:
            token (str): The final token
            freq_list (FrequencyList): Dataclass object that contains normal, header,
            and title frequency for a token in a page. Also includes the total occurences of that specific token on the page

        """        
        tf_score = self.calculate_tf_score(freq_list)
        
        if token not in self.index:
            self.index[token] = []
        self.index[token].append((self.current_doc_id, tf_score))

    def start_new_document(self, url: str, total_tokens: int) -> int:
        """Updates InvertedIndex instance variables for new document

        Args:
            url (str): url of current document
            total_tokens (int): total tokens of current document

        Returns:
            doc_id (int): doc_id of the current document
        """
        doc_id = self.id_counter
        self.id_counter += 1
        self.current_doc_id = doc_id
        self.current_url = url

        self.id_map[doc_id] = DocumentInfo(
            id=doc_id,
            url=url,
            total_tokens=total_tokens
        )

        return doc_id

    def calculate_tf_score(self, freq_list : FrequencyList) -> float:
        """This function calculates the tf_score of a token given a FrequencyList

        Args:
            freq_list (FrequencyList): Dataclass object that contains normal, header,
            and title frequency for a token in a page. Also includes the total occurences of that specific token on the page

        Returns:
            float: The tf score for the FrequencyList
        """        

        doc_len = self.id_map[self.current_doc_id].total_tokens

        weights = {
            "normal" : 1,
            "title" : 5,
            "heading" : 10
        }

        normal_points = freq_list.normal * weights["normal"]
        title_points = freq_list.title * weights["title"]
        header_points = freq_list.heading * weights["heading"]

        total = (normal_points + title_points + header_points) / max(1, doc_len)

        return total

    def calculate_idf(self, token: str) -> float:
        """Calculates the idf score for the specific token (used during retrieval)

        Args:
            token (str): associated token for idf scoring

        Returns:
            float: idf score for associated token
        """

        # Get number of indexed documents, and number of documents the specific token shows up in
        N = self.id_counter
        doc_freq = len(self.index.get(token, []))

        if doc_freq == 0:
            return 0.0

        return math.log(N / doc_freq)

    def ranked_search(self, query: list[str], k: int = 10) -> list[tuple[str, float]]:

        """Returns the K most relevant queries using ranked search

        Args:
            query (list[str]): list of tokens from the query
            k (int): number of relevant documents to return

        Returns:
            results (list[tuple[str, float]]): Most relevant results (url, score)
        """
        # Stores the scores for each document
        scores = {}

        # Iterates through each token in the query
        for token in query:

            # Skip if token is not in the index
            if token not in self.index:
                continue

            # Calculate idf score for associated token
            idf = self.calculate_idf(token)

            # Iterate through list of postings for that associated token
            for doc_id, tf in self.index[token]:

                # Total score for each document is the tf * idf for each token
                score = tf * idf
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        # Sort the scores by decreasing order
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Returning the K highest ranked items
        results = []
        for doc_id, score in ranked[:k]:
            url = self.id_map[doc_id].url
            results.append((url, score))

        return results

    def boolean_search(self, query: list[str]) -> list[str]:

        """Performs a boolean search using AND with the query tokens

        Args:
            query (list[str]): list of tokens from the query

        Returns:
            results (list[str]): list of urls that contain all query tokens
        """
        # Empty query returns an empty list
        if not query:
            return []

        posting_lists = []

        # Creating a list of lists, each list containing the docs for each token
        for token in query:
            if token not in self.index:
                return []
            docs = {doc_id for doc_id, tf in self.index[token]}
            posting_lists.append(docs)

        # Unwrapping the posting_lists and performing AND operation
        if len(posting_lists) == 1:
            common_docs = posting_lists[0]
        else:
            common_docs = set.intersection(*posting_lists)

        results = [self.id_map[doc_id].url for doc_id in common_docs]

        return results
