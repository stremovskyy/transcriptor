from rapidfuzz import process, fuzz
from typing import List, Dict, Any, Optional, Set
from logging import getLogger
from functools import lru_cache
import re

logger = getLogger(__name__)


class KeyWordsService:
    """Service for spotting keywords in transcription results."""

    # Precompile regex for word splitting
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
            keywords: List of keywords to look for
            languages: List of languages to process
            confidence_threshold: Minimum confidence level to consider a match

        Returns:
            Dictionary of keyword matches with timing information
        """
        # Early return if no keywords provided
        if not keywords:
            logger.info("No keywords provided for spotting")
            return {lang: {} for lang in languages}

        # Convert keywords to lowercase for case-insensitive matching
        normalized_keywords = [keyword.lower() for keyword in keywords]
        logger.info(f"Processing keywords: {keywords}")

        # Initialize result dictionary
        keyword_spots = {
            lang: {keyword: [] for keyword in keywords}
            for lang in languages
        }

        # Process each language
        for language in languages:
            segments = transcription_results.get(language, [])

            if not segments:
                logger.info(f"No segments found for language: {language}")
                continue

            for segment_data in segments:
                KeyWordsService._process_segment(
                    segment_data,
                    keywords,
                    normalized_keywords,
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
            confidence_threshold: int
    ) -> None:
        """Process a single transcription segment for keywords."""
        segment_text = segment_data["text"]
        segment_start = segment_data["start"]
        segment_duration = segment_data["end"] - segment_data["start"]

        # Use word timestamps if available for more precise keyword spotting
        if "words" in segment_data and segment_data["words"]:
            KeyWordsService._spot_keywords_with_timestamps(
                segment_data["words"],
                original_keywords,
                normalized_keywords,
                keyword_spots,
                confidence_threshold,
                segment_text
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
                segment_duration
            )

    @staticmethod
    def _spot_keywords_with_timestamps(
            words_with_times: List[Dict[str, Any]],
            original_keywords: List[str],
            normalized_keywords: List[str],
            keyword_spots: Dict[str, List[Dict[str, Any]]],
            confidence_threshold: int,
            context: str
    ) -> None:
        """Spot keywords using word-level timestamps."""
        for i, (orig_keyword, norm_keyword) in enumerate(zip(original_keywords, normalized_keywords)):
            for word_info in words_with_times:
                word = word_info["word"]
                norm_word = word.lower()

                # First try exact match for efficiency
                if norm_keyword == norm_word:
                    similarity = 100
                else:
                    # Fall back to fuzzy matching if needed
                    similarity = fuzz.ratio(norm_keyword, norm_word)

                if similarity >= confidence_threshold:
                    keyword_spots[orig_keyword].append({
                        'word': word,
                        'confidence': similarity,
                        'time_mark': round(word_info["start"], 2),
                        'duration': round(word_info["end"] - word_info["start"], 2),
                        'context': context  # Add broader context
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
            segment_duration: float
    ) -> None:
        """Spot keywords without word-level timestamps."""
        words = KeyWordsService._word_splitter.split(segment_text)

        # Convert words list to string for caching function
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
                    # Calculate time relative to segment
                    relative_time = (index / len(words)) * segment_duration
                    # Add segment start time for absolute position
                    absolute_time = segment_start + relative_time

                    # Get context (words before and after)
                    context_start = max(0, index - 2)
                    context_end = min(len(words), index + 3)
                    context = ' '.join(words[context_start:context_end])

                    keyword_spots[orig_keyword].append({
                        'word': word,
                        'confidence': score,
                        'time_mark': round(absolute_time, 2),
                        'context': context
                    })