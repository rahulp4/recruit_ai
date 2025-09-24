from typing import Dict, List, Any, Tuple, Type, Optional, Union
from pydantic import BaseModel, Field
# Assuming .plugins.base imports BasePlugin, PluginMetadata, PluginCategory
from matchai.plugins.base import BasePlugin, PluginMetadata, PluginCategory
import logging
import spacy # New import
import rapidfuzz.fuzz # New import
import nltk
from nltk.corpus import wordnet # New import
import re # New import for regex patterns
import os

# --- Helper Models for Detailed Results ---
class MatchedKeywordDetail(BaseModel):
    """Detailed information for a keyword that was found."""
    keyword: str = Field(description="The primary keyword found.")
    matched_form_in_text: str = Field(
        description="The specific form from the resume text that triggered the match "
                    "(e.g., original word, lemmatized form, or fuzzy match)."
    )
    match_type: str = Field(
        description="How the keyword was matched "
                    "(e.g., 'exact_phrase', 'exact_word', 'lemmatized_word', "
                    "'wordnet_synonym_lemma', 'wordnet_synonym_exact', 'fuzzy_match')."
    )
    weight: int = Field(description="The importance weight of the matched keyword.")

class MissingKeywordDetail(BaseModel):
    """Detailed information for a keyword that was not found."""
    keyword: str = Field(description="The primary keyword that was missing.")
    weight: int = Field(description="The importance weight of the missing keyword.")

# --- This is the updated KeywordMatchResult Model that needs to be at the top ---
class KeywordMatchResult(BaseModel):
    """Model for comprehensive keyword matching results."""
    overall_match_score: float = Field( # Updated name from 'match_score'
        0.0,
        description="Overall weighted match score as a percentage (0-100)."
    )
    category_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Weighted match scores by category."
    )
    
    # New fields for detailed results
    matched_details: Dict[str, List[MatchedKeywordDetail]] = Field(
        default_factory=dict,
        description="Detailed information about keywords found in the resume, grouped by category."
    )
    missing_details: Dict[str, List[MissingKeywordDetail]] = Field(
        default_factory=dict,
        description="Detailed information about keywords not found in the resume, grouped by category."
    )
    
    # New fields for score breakdown
    total_possible_score: float = Field(
        0.0,
        description="The sum of weights of all keywords configured."
    )
    total_achieved_score: float = Field(
        0.0,
        description="The sum of weights of keywords actually matched."
    )
    
    # Summary lists (optional, but good for a quick overview, kept for backward compatibility)
    matched_keywords: List[str] = Field(
        default_factory=list,
        description="List of primary keywords (strings) that were found in the resume."
    )
    missing_keywords: List[str] = Field(
        default_factory=list,
        description="List of primary keywords (strings) that were not found in the resume."
    )


# --- Helper Models (assuming these are defined correctly above this class) ---
# class MatchedKeywordDetail(BaseModel): ...
# class MissingKeywordDetail(BaseModel): ...
# class KeywordMatchResult(BaseModel): ...

# --- Updated KeywordMatcherPlugin Class ---
logger = logging.getLogger(__name__)

class KeywordMatcherPlugin(BasePlugin):
    """Plugin for matching job-specific keywords in resumes with advanced NLP."""
    
    DEFAULT_KEYWORDS = {
        "technical_skills": [
            "java", "angular", "MySQL", "aws", "python", "docker", "kubernetes", "machine learning"
        ],
        "soft_skills": [
            "leadership", "communication", "teamwork", "problem solving",
            "time management", "creativity", "adaptability", "negotiation"
        ],
        "certifications": [
            "aws certified", "google cloud", "microsoft certified", 
            "cisco certified", "pmp", "scrum"
        ]
    }
    
    # --- New Properties for NLP and Keyword Handling (Add self.keywords here too) ---
    _custom_keywords_config: Optional[Dict[str, List[Dict[str, Union[str, int, List[str]]]]]]
    nlp: Any
    FUZZY_THRESHOLD: int
    wordnet_synonym_cache: Dict[str, List[str]]
    
    keywords: Dict[str, List[Dict[str, Union[str, int, List[str]]]]] # Ensure this property is declared
    # --- End New Properties ---

    def __init__(self, llm_service=None, keywords_config: Optional[Dict[str, List[Dict[str, Union[str, int, List[str]]]]]] = None):
        """
        Initialize the plugin with an LLM service and optionally a custom keyword configuration.
        Also sets up NLP models and caches WordNet synonyms.
        """
        # DEBUG print for NLTK_DATA is useful, keep it if needed for diagnostics
        # print(f"DEBUG: os.environ['NLTK_DATA'] = {os.environ.get('NLTK_DATA')}")
        
        self.llm_service = llm_service
        self._custom_keywords_config = keywords_config

        # --- FIX START ---
        # Initialize self.keywords here to ensure the attribute always exists
        self.keywords = {} 
        # --- FIX END ---

        self.nlp = None
        self.FUZZY_THRESHOLD = 88 
        self.wordnet_synonym_cache = {}
        
        # Load spaCy NLP model during initialization
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logging.info("spaCy 'en_core_web_sm' model loaded successfully.")
        except OSError:
            logging.error(
                "spaCy model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )
        
        logging.debug(f"{self.metadata.name} called init for llm {self.llm_service}");

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="keyword_matcher",
            version="2.0.0", # Updated version due to significant changes
            description="Matches job-specific keywords in resumes with advanced NLP (lemmatization, implicit synonyms, fuzzy matching).",
            category=PluginCategory.CUSTOM,
            author="Resume Analysis Team"
        )
    
    def initialize(self) -> None:
        """
        Initialize the plugin's keywords and pre-process WordNet synonyms.
        """
        logging.info(f"Initializing {self.metadata.name}")
        
        # Now, self.keywords already exists (as an empty dict), so we can safely populate it.
        if self._custom_keywords_config:
            self.keywords = self._custom_keywords_config
            logging.info("Using custom keyword configuration provided during instantiation.")
        else:
            # Transform DEFAULT_KEYWORDS (simple list) into the structured format
            self.keywords.clear() # Clear it before populating if it's from default
            for category, kws in self.DEFAULT_KEYWORDS.items():
                self.keywords[category] = []
                for keyword_str in kws:
                    self.keywords[category].append({
                        "keyword": keyword_str,
                        "weight": 1,        # Default weight
                        "variations": [],   # No explicit variations by default in DEFAULT_KEYWORDS
                        # "synonyms": []    # No explicit synonyms as per user request (handled implicitly by WordNet)
                    })
            logging.info("Using transformed DEFAULT_KEYWORDS.")
        
        # Pre-process WordNet synonyms for all configured keywords (cached for performance)
        try:
            # Verify WordNet data is available
            nltk.data.find('corpora/wordnet')
            nltk.data.find('corpora/omw-1.4')

            for category, keywords_list in self.keywords.items(): # This line should now work
                for kw_config in keywords_list:
                    primary_keyword = kw_config["keyword"].lower()
                    all_forms_for_wordnet = [primary_keyword] + \
                                            [v.lower() for v in kw_config.get("variations", [])]
                    
                    for form in all_forms_for_wordnet:
                        if " " not in form: # Only pre-compute for single words, as WordNet synsets are primarily word-based
                            if form not in self.wordnet_synonym_cache: 
                                self.wordnet_synonym_cache[form] = {} # Initialize nested dict for POS-specific synonyms

                            if self.nlp:
                                form_doc = self.nlp(form)
                                if len(form_doc) > 0 and form_doc[0].is_alpha:
                                    inferred_spacy_pos = form_doc[0].pos_
                                    wordnet_pos_tag = self._get_wordnet_pos(inferred_spacy_pos)
                                    
                                    if wordnet_pos_tag and wordnet_pos_tag not in self.wordnet_synonym_cache[form]:
                                        synonyms_for_form_pos = set()
                                        for synset in wordnet.synsets(form, pos=wordnet_pos_tag):
                                            for lemma in synset.lemmas():
                                                synonyms_for_form_pos.add(lemma.name().lower())
                                        
                                        self.wordnet_synonym_cache[form][wordnet_pos_tag] = list(synonyms_for_form_pos)
            
            logging.info("WordNet synonyms pre-processed and cached (POS-aware).")
        except LookupError:
            logging.warning(
                "WordNet data not found. Implicit synonym matching (via WordNet) will be disabled. "
                "Please run: python -m nltk.downloader wordnet omw-1.4"
            )
        except Exception as e:
            logging.error(f"Error during WordNet synonym pre-processing: {e}")
            self.wordnet_synonym_cache = {} 

    # --- Add the _get_wordnet_pos helper method here ---
    def _get_wordnet_pos(self, spacy_pos: str) -> Optional[str]:
        """
        Maps spaCy POS tags to WordNet POS tags.
        WordNet primarily uses NOUN, VERB, ADJ, ADV.
        """
        if spacy_pos.startswith('N'): return wordnet.NOUN
        if spacy_pos.startswith('V'): return wordnet.VERB
        if spacy_pos.startswith('ADJ'): return wordnet.ADJ
        if spacy_pos.startswith('ADV'): return wordnet.ADV
        return None 
    # --- End helper method ---

    def get_model(self) -> Type[BaseModel]:
        """Get the Pydantic model for the keyword matcher."""
        return KeywordMatchResult
    
    def process_resume(self, resume: Any, text: str) -> Dict[str, Any]:
        """
        Process a resume to match keywords using a multi-layered NLP approach:
        1. Exact (phrase/word) match.
        2. Lemmatized word match.
        3. WordNet implicit synonym match.
        4. Fuzzy match (for typos).
        
        Args:
            resume: The Resume object (expected to have 'file_name' attribute).
            text: The raw text from the resume.
            
        Returns:
            KeywordMatchResult: A Pydantic model instance with comprehensive keyword matching results.
        """
        resume_name = getattr(resume, 'file_name', 'Unnamed Resume')
        logging.info(f"Starting advanced keyword matching for resume: {resume_name}")

        text_lower = text.lower()
        
        text_tokens_with_pos = [] 
        text_lemmas_lower_set = set() 

        if self.nlp:
            doc = self.nlp(text_lower)
            for token in doc:
                if token.is_alpha: 
                    text_tokens_with_pos.append((token.text, token.lemma_, token.pos_))
                    text_lemmas_lower_set.add(token.lemma_)
            logging.debug(f"Resume text tokenized into {len(text_tokens_with_pos)} tokens.")
        else:
            logging.warning("spaCy NLP model not loaded. Lemmatization, POS-aware WordNet, and Fuzzy Matching will be disabled.")
            text_tokens_with_pos = [(w, w, 'UNKNOWN') for w in re.findall(r'\b\w+\b', text_lower)]
            text_lemmas_lower_set = set(w for w, _, _ in text_tokens_with_pos)

        results = KeywordMatchResult() 

        for category, keywords_list in self.keywords.items():
            category_total_weight = 0.0
            category_achieved_weight = 0.0

            results.matched_details[category] = []
            results.missing_details[category] = []

            for kw_config in keywords_list:
                primary_keyword = kw_config["keyword"]
                weight = kw_config.get("weight", 1)
                explicit_variations = [v.lower() for v in kw_config.get("variations", [])]
                
                all_forms_to_check = [primary_keyword.lower()] + explicit_variations
                
                all_forms_lemmatized = []
                if self.nlp:
                    for form in all_forms_to_check:
                        lemma_doc = self.nlp(form)
                        if len(lemma_doc) > 0 and lemma_doc[0].is_alpha:
                            all_forms_lemmatized.append(lemma_doc[0].lemma_)
                
                is_matched = False
                matched_form_in_text = None
                match_type = None

                category_total_weight += weight
                results.total_possible_score += weight

                # --- Matching Strategy (Prioritized: Exact > Lemmatized > WordNet > Fuzzy) ---

                # 1. Exact Match (Phrase or Whole-Word) for all forms
                for form_to_check in all_forms_to_check:
                    if " " in form_to_check: 
                        if form_to_check in text_lower:
                            is_matched = True
                            matched_form_in_text = form_to_check
                            match_type = "exact_phrase"
                            break
                    else: 
                        pattern = r'\b' + re.escape(form_to_check) + r'\b'
                        if re.search(pattern, text_lower):
                            is_matched = True
                            matched_form_in_text = form_to_check
                            match_type = "exact_word"
                            break
                
                # 2. Lemmatized Whole-Word Match (if not already matched and NLP enabled)
                if not is_matched and self.nlp:
                    for form_lemma in all_forms_lemmatized:
                        if form_lemma in text_lemmas_lower_set:
                            for text_token_text, text_token_lemma, text_token_pos in text_tokens_with_pos:
                                if text_token_lemma == form_lemma:
                                    keyword_doc = self.nlp(form_lemma)
                                    if len(keyword_doc) > 0 and keyword_doc[0].is_alpha:
                                        expected_spacy_pos = keyword_doc[0].pos_
                                        if text_token_pos == expected_spacy_pos:
                                            is_matched = True
                                            matched_form_in_text = text_token_text
                                            match_type = "lemmatized_word_pos_aware"
                                            break
                            if is_matched:
                                break

                # 3. WordNet Synonyms Match (if not already matched and WordNet is available)
                if not is_matched and self.wordnet_synonym_cache:
                    forms_for_wordnet_lookup = [f for f in all_forms_to_check if " " not in f]
                    
                    for form_for_lookup in forms_for_wordnet_lookup:
                        expected_spacy_pos_for_lookup = None
                        if self.nlp:
                            lookup_doc = self.nlp(form_for_lookup)
                            if len(lookup_doc) > 0 and lookup_doc[0].is_alpha:
                                expected_spacy_pos_for_lookup = lookup_doc[0].pos_
                        
                        if not expected_spacy_pos_for_lookup:
                            continue

                        wordnet_pos_tag = self._get_wordnet_pos(expected_spacy_pos_for_lookup)
                        if not wordnet_pos_tag:
                            continue
                        
                        synonyms_for_lookup = self.wordnet_synonym_cache.get(form_for_lookup, {}).get(wordnet_pos_tag, [])
                        
                        for wordnet_synonym_lemma in synonyms_for_lookup:
                            for text_token_text, text_token_lemma, text_token_pos in text_tokens_with_pos:
                                if (text_token_lemma == wordnet_synonym_lemma and 
                                    text_token_pos == expected_spacy_pos_for_lookup):
                                    is_matched = True
                                    matched_form_in_text = text_token_text
                                    match_type = "wordnet_synonym_pos_aware"
                                    break
                            if is_matched:
                                break
                        if is_matched:
                            break

                # 4. Fuzzy Matching (if not already matched, as a last resort)
                if not is_matched:
                    for form_to_check in all_forms_to_check:
                        for text_token_text, _, _ in text_tokens_with_pos: 
                            similarity_score = rapidfuzz.fuzz.ratio(form_to_check, text_token_text)
                            if similarity_score >= self.FUZZY_THRESHOLD:
                                is_matched = True
                                matched_form_in_text = text_token_text
                                match_type = "fuzzy_match"
                                break
                        if is_matched:
                            break

                # --- Record Results ---
                if is_matched:
                    results.matched_keywords.append(primary_keyword)
                    results.matched_details[category].append(MatchedKeywordDetail(
                        keyword=primary_keyword,
                        matched_form_in_text=matched_form_in_text,
                        match_type=match_type,
                        weight=weight
                    ))
                    category_achieved_weight += weight
                    results.total_achieved_score += weight
                else:
                    results.missing_keywords.append(primary_keyword)
                    results.missing_details[category].append(MissingKeywordDetail(
                        keyword=primary_keyword,
                        weight=weight
                    ))

            # Calculate category score
            category_score_percent = 0.0
            if category_total_weight > 0:
                category_score_percent = (category_achieved_weight / category_total_weight) * 100
            results.category_scores[category] = round(category_score_percent, 2)

        # Calculate overall match score
        if results.total_possible_score > 0:
            results.overall_match_score = round((results.total_achieved_score / results.total_possible_score) * 100, 2)
        else:
            results.overall_match_score = 0.0

        logging.info(f"Keyword match complete for {resume_name}. Overall score: {results.overall_match_score}%")

        return results