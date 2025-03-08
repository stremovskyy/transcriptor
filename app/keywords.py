from rapidfuzz import process, fuzz
from typing import List, Dict, Any, Optional, Set, Tuple
from logging import getLogger
from functools import lru_cache
import re

logger = getLogger(__name__)


class KeyWordsService:
    """Service for spotting keywords and negated keywords in transcription results."""

    _word_splitter = re.compile(r'\s+')

    @staticmethod
    def spot_keywords(
            transcription_results: Dict[str, Any],
            keywords: List[str],
            languages: List[str],
            confidence_threshold: int = 80
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Process keywords from transcription results

        Args:
            transcription_results: Dictionary containing transcription segments with timing information
            keywords: List of keywords to look for (can include negated keywords with "!" prefix)
            languages: List of languages to process
            confidence_threshold: Minimum confidence level to consider a match

        Returns:
            Dictionary of keyword matches with timing information
        """
        if not keywords:
            logger.info("No keywords provided for spotting")
            return {lang: {} for lang in languages}

        # Separate regular keywords from negated keywords
        regular_keywords = []
        negated_keywords = []
        display_keywords = []  # Original keywords for display

        for keyword in keywords:
            if keyword.startswith('!'):
                negated_keywords.append(keyword[1:].lower())  # Remove '!' and lowercase
                display_keywords.append(keyword)  # Keep original for display
            else:
                regular_keywords.append(keyword.lower())
                display_keywords.append(keyword)

        logger.info(f"Processing keywords: {display_keywords}")
        logger.info(f"Regular keywords: {[kw for kw in keywords if not kw.startswith('!')]}")
        logger.info(f"Negated keywords: {[kw for kw in keywords if kw.startswith('!')]}")

        keyword_spots = {
            lang: {keyword: [] for keyword in display_keywords}
            for lang in languages
        }

        for language in languages:
            segments = transcription_results.get(language, [])

            if not segments:
                logger.info(f"No segments found for language: {language}")
                continue

            for segment_data in segments:
                # Process regular keywords
                if regular_keywords:
                    KeyWordsService._process_segment(
                        segment_data,
                        [kw for kw in keywords if not kw.startswith('!')],
                        regular_keywords,
                        keyword_spots[language],
                        confidence_threshold,
                        is_negated=False
                    )

                # Process negated keywords
                if negated_keywords:
                    KeyWordsService._process_segment_negation(
                        segment_data,
                        [kw for kw in keywords if kw.startswith('!')],
                        negated_keywords,
                        keyword_spots[language],
                        confidence_threshold
                    )

        return keyword_spots

    @staticmethod
    def _process_segment(
            segment_data: Dict[str, Any],
            original_keywords: List[str],
            normalized_keywords: List[str],
            keyword_spots: Dict[str, List[Dict[str, Any]]],
            confidence_threshold: int,
            is_negated: bool = False
    ) -> None:
        """Process a single transcription segment for keywords."""
        segment_text = segment_data["text"]
        segment_start = segment_data["start"]
        segment_duration = segment_data["end"] - segment_data["start"]

        if "words" in segment_data and segment_data["words"]:
            KeyWordsService._spot_keywords_with_timestamps(
                segment_data["words"],
                original_keywords,
                normalized_keywords,
                keyword_spots,
                confidence_threshold,
                segment_text,
                is_negated
            )
        else:
            # Fallback to traditional method if word timestamps not available
            KeyWordsService._spot_keywords_without_timestamps(
                segment_text,
                original_keywords,
                normalized_keywords,
                keyword_spots,
                confidence_threshold,
                segment_start,
                segment_duration,
                is_negated
            )

    @staticmethod
    def _process_segment_negation(
            segment_data: Dict[str, Any],
            original_keywords: List[str],  # These include '!' prefix
            normalized_keywords: List[str],  # These are without '!' prefix but lowercased
            keyword_spots: Dict[str, List[Dict[str, Any]]],
            confidence_threshold: int
    ) -> None:
        """Process a segment for negated keywords (marking segments where keywords are NOT found)."""
        segment_text = segment_data["text"].lower()
        segment_start = segment_data["start"]
        segment_end = segment_data["end"]

        # For each negated keyword, check if it's NOT in the segment
        for i, (orig_keyword, norm_keyword) in enumerate(zip(original_keywords, normalized_keywords)):
            # Check if the keyword is NOT present in this segment
            keyword_found = False

            # First check exact match
            if norm_keyword in segment_text:
                keyword_found = True
            else:
                # Then check fuzzy matches
                words = KeyWordsService._word_splitter.split(segment_text)
                words_str = '|'.join(words)

                matches = KeyWordsService._get_fuzzy_matches(
                    norm_keyword,
                    words_str,
                    confidence_threshold,
                    limit=5
                )

                for _, score, _ in matches:
                    if score >= confidence_threshold:
                        keyword_found = True
                        break

            # If keyword is NOT found, this is a match for the negated keyword
            if not keyword_found:
                keyword_spots[orig_keyword].append({
                    'negated_match': True,
                    'confidence': 100,  # High confidence for negated matches
                    'time_mark': round(segment_start, 2),
                    'duration': round(segment_end - segment_start, 2),
                    'context': segment_data["text"]
                })

    @staticmethod
    def _spot_keywords_with_timestamps(
            words_with_times: List[Dict[str, Any]],
            original_keywords: List[str],
            normalized_keywords: List[str],
            keyword_spots: Dict[str, List[Dict[str, Any]]],
            confidence_threshold: int,
            context: str,
            is_negated: bool = False
    ) -> None:
        """Spot keywords using word-level timestamps."""
        for i, (orig_keyword, norm_keyword) in enumerate(zip(original_keywords, normalized_keywords)):
            for word_info in words_with_times:
                word = word_info["word"]
                norm_word = word.lower()

                if norm_keyword == norm_word:
                    similarity = 100
                else:
                    similarity = fuzz.ratio(norm_keyword, norm_word)

                if similarity >= confidence_threshold:
                    keyword_spots[orig_keyword].append({
                        'word': word,
                        'confidence': similarity,
                        'time_mark': round(word_info["start"], 2),
                        'duration': round(word_info["end"] - word_info["start"], 2),
                        'context': context,  # Add broader context
                        'negated_match': is_negated
                    })

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_fuzzy_matches(query: str, target_list: str, threshold: int, limit: int = 10):
        """Cached fuzzy matching to avoid redundant computation."""
        # Convert target_list string to actual list (needed for caching)
        targets = target_list.split('|')
        return process.extract(
            query,
            targets,
            scorer=fuzz.ratio,
            limit=limit
        )

    @staticmethod
    def _spot_keywords_without_timestamps(
            segment_text: str,
            original_keywords: List[str],
            normalized_keywords: List[str],
            keyword_spots: Dict[str, List[Dict[str, Any]]],
            confidence_threshold: int,
            segment_start: float,
            segment_duration: float,
            is_negated: bool = False
    ) -> None:
        """Spot keywords without word-level timestamps."""
        words = KeyWordsService._word_splitter.split(segment_text)

        words_str = '|'.join(words)

        for i, (orig_keyword, norm_keyword) in enumerate(zip(original_keywords, normalized_keywords)):
            matches = KeyWordsService._get_fuzzy_matches(
                norm_keyword,
                words_str,
                confidence_threshold,
                limit=10
            )

            for word, score, index in matches:
                if score >= confidence_threshold:
                    relative_time = (index / len(words)) * segment_duration
                    absolute_time = segment_start + relative_time

                    # Get context (words before and after)
                    context_start = max(0, index - 2)
                    context_end = min(len(words), index + 3)
                    context = ' '.join(words[context_start:context_end])

                    keyword_spots[orig_keyword].append({
                        'word': word,
                        'confidence': score,
                        'time_mark': round(absolute_time, 2),
                        'context': context,
                        'negated_match': is_negated
                    })