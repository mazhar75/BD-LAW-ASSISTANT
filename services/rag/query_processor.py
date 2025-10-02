"""
Query processor for enhancing search quality in FAISS-RAG pipeline
"""
import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process and enhance queries before FAISS search"""

    def __init__(self):
        # Greeting patterns that shouldn't trigger search
        self.greeting_patterns = [
            r'^(hi|hello|hey|greetings?)$',
            r'^(good\s+(morning|afternoon|evening|night))$',
            r'^(how\s+are\s+you|whats?\s+up)$',
            r'^(thanks?|thank\s+you)$',
            r'^(bye|goodbye|see\s+you)$'
        ]

        # Legal domain keywords for query expansion
        self.legal_synonyms = {
            'murder': ['homicide', 'killing', 'manslaughter', 'death penalty', 'section 302', 'section 300'],
            'stealing': ['theft', 'robbery', 'larceny', 'burglary', 'section 378', 'stolen property'],
            'property': ['land', 'real estate', 'immovable property', 'transfer', 'ownership', 'possession'],
            'marriage': ['matrimony', 'wedding', 'divorce', 'spouse', 'husband', 'wife', 'matrimonial'],
            'contract': ['agreement', 'deed', 'covenant', 'obligation', 'breach', 'performance'],
            'criminal': ['crime', 'offense', 'penal', 'punishment', 'imprisonment', 'conviction'],
            'assault': ['battery', 'hurt', 'injury', 'violence', 'force', 'section 351'],
            'fraud': ['cheating', 'deception', 'forgery', 'misrepresentation', 'section 415']
        }

        # Query templates for common patterns
        self.query_templates = {
            'definition': ['what is', 'define', 'meaning of', 'definition of'],
            'punishment': ['punishment for', 'penalty for', 'sentence for', 'what happens if'],
            'procedure': ['how to', 'process for', 'procedure for', 'steps to'],
            'rights': ['rights of', 'entitled to', 'can i', 'am i allowed'],
            'laws': ['laws for', 'law about', 'legal provision', 'section about']
        }

        # Stop words to remove (Bangladesh legal context)
        self.stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had'}

    def is_greeting(self, query: str) -> bool:
        """Check if query is just a greeting"""
        query_lower = query.lower().strip()
        for pattern in self.greeting_patterns:
            if re.match(pattern, query_lower):
                return True
        return False

    def classify_query_intent(self, query: str) -> str:
        """Classify the intent of the query"""
        query_lower = query.lower()

        # Check for specific intents
        if any(template in query_lower for template in self.query_templates['definition']):
            return 'definition'
        elif any(template in query_lower for template in self.query_templates['punishment']):
            return 'punishment'
        elif any(template in query_lower for template in self.query_templates['procedure']):
            return 'procedure'
        elif any(template in query_lower for template in self.query_templates['rights']):
            return 'rights'
        elif any(template in query_lower for template in self.query_templates['laws']):
            return 'laws'
        else:
            return 'general'

    def expand_query(self, query: str) -> str:
        """Expand query with legal synonyms and related terms"""
        query_lower = query.lower()
        expanded_terms = []

        # Find matching keywords and add synonyms
        for key, synonyms in self.legal_synonyms.items():
            if key in query_lower:
                # Add original term and top 2 synonyms
                expanded_terms.extend(synonyms[:2])

        # Combine original query with expansions
        if expanded_terms:
            expansion = ' OR '.join(expanded_terms)
            enhanced_query = f"{query} {expansion}"
            logger.info(f"Expanded query: {query} -> {enhanced_query}")
            return enhanced_query

        return query

    def extract_section_numbers(self, query: str) -> List[str]:
        """Extract legal section numbers from query"""
        # Pattern for section numbers (e.g., "section 302", "s. 420", "sec 144")
        section_patterns = [
            r'section\s*(\d+[a-z]?)',
            r'sec\s*\.?\s*(\d+[a-z]?)',
            r's\s*\.?\s*(\d+[a-z]?)',
            r'article\s*(\d+[a-z]?)',
            r'act\s*(\d+)'
        ]

        sections = []
        for pattern in section_patterns:
            matches = re.findall(pattern, query.lower())
            sections.extend(matches)

        return sections

    def clean_query(self, query: str) -> str:
        """Clean and normalize the query"""
        # Remove extra spaces
        query = ' '.join(query.split())

        # Remove special characters except those in legal context
        query = re.sub(r'[^\w\s\.\-\/]', ' ', query)

        # Remove stop words for better matching
        words = query.split()
        filtered_words = [w for w in words if w.lower() not in self.stop_words or len(words) <= 3]

        return ' '.join(filtered_words)

    def reformulate_query(self, query: str, intent: str) -> str:
        """Reformulate query based on intent for better results"""
        query_lower = query.lower()

        if intent == 'punishment':
            # Add legal context for punishment queries
            if 'murder' in query_lower:
                return f"{query} penal code section 302 homicide death penalty life imprisonment"
            elif 'theft' in query_lower or 'stealing' in query_lower:
                return f"{query} penal code section 378 379 380 theft property stolen"
            elif 'assault' in query_lower:
                return f"{query} hurt injury section 351 352 criminal force"

        elif intent == 'definition':
            # Add definitional context
            base_query = re.sub(r'what is|define|meaning of|definition of', '', query_lower).strip()
            return f"definition {base_query} means defined as under section act"

        elif intent == 'rights':
            # Add rights-related context
            return f"{query} entitled right privilege protection under law"

        elif intent == 'procedure':
            # Add procedural context
            return f"{query} procedure process steps application filing court"

        return query

    def process_query(self, query: str) -> Tuple[str, Dict]:
        """Main processing pipeline"""
        # Check if it's a greeting
        if self.is_greeting(query):
            return None, {
                'is_greeting': True,
                'original_query': query,
                'message': 'Greeting detected - no search needed'
            }

        # Extract metadata
        intent = self.classify_query_intent(query)
        sections = self.extract_section_numbers(query)

        # Clean the query
        cleaned_query = self.clean_query(query)

        # Expand with synonyms
        expanded_query = self.expand_query(cleaned_query)

        # Reformulate based on intent
        final_query = self.reformulate_query(expanded_query, intent)

        metadata = {
            'is_greeting': False,
            'original_query': query,
            'processed_query': final_query,
            'intent': intent,
            'sections_mentioned': sections,
            'has_expansion': expanded_query != cleaned_query
        }

        logger.info(f"Query processing: '{query}' -> '{final_query}' (intent: {intent})")

        return final_query, metadata


# Example usage and testing
if __name__ == "__main__":
    processor = QueryProcessor()

    test_queries = [
        "hi",
        "hello there",
        "what are the laws for murder?",
        "what are the laws for stealing?",
        "punishment for theft under section 378",
        "how to file a property case",
        "define contract",
        "what is homicide",
        "rights of accused person"
    ]

    print("Query Processing Examples:\n")
    for query in test_queries:
        processed, metadata = processor.process_query(query)
        print(f"Original: {query}")
        if metadata['is_greeting']:
            print(f"Result: {metadata['message']}")
        else:
            print(f"Processed: {processed}")
            print(f"Intent: {metadata['intent']}")
            if metadata['sections_mentioned']:
                print(f"Sections: {metadata['sections_mentioned']}")
        print("-" * 50)