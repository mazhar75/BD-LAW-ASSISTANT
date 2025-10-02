"""
Prompt templates for Bangladesh Law Assistant RAG pipeline
Optimized for legal domain with support for Bengali and English
"""

from langchain.prompts import PromptTemplate

# Main QA prompt for legal questions
LEGAL_QA_PROMPT = PromptTemplate(
    template="""You are an expert Bangladesh law assistant with comprehensive knowledge of the Bangladesh legal system, including acts, ordinances, and regulations. Your role is to provide accurate, helpful, and legally sound information based on the context provided.

Context from Bangladesh Laws:
{context}

Question: {question}

Instructions:
1. Base your answer strictly on the provided context from Bangladesh laws
2. If the context contains relevant information, provide a detailed and accurate answer
3. Cite specific acts, sections, or provisions when applicable
4. If the context doesn't contain sufficient information, clearly state that
5. Use clear, professional language suitable for both legal professionals and general public
6. If relevant, mention any recent amendments or updates mentioned in the context
7. For Bengali text in context, provide appropriate translation or explanation

Answer:""",
    input_variables=["context", "question"]
)

# Chat prompt for conversational interactions
LEGAL_CHAT_PROMPT = PromptTemplate(
    template="""You are an expert Bangladesh law assistant engaged in a helpful conversation about Bangladesh laws and legal matters. Use the following pieces of context and chat history to answer the question at the end.

Context from Bangladesh Laws:
{context}

Chat History:
{chat_history}

Human Question: {question}

Instructions:
1. Provide accurate legal information based on Bangladesh law
2. Reference specific acts, sections, and provisions when applicable
3. Consider the chat history for context continuity
4. Be conversational while maintaining legal accuracy
5. If you need clarification, ask follow-up questions
6. Acknowledge when information is outside your knowledge base
7. Provide examples or explanations when helpful for understanding

Assistant Response:""",
    input_variables=["context", "chat_history", "question"]
)

# Prompt for condensing follow-up questions
CONDENSE_QUESTION_PROMPT = PromptTemplate(
    template="""Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question that captures all relevant context for searching Bangladesh law documents.

Chat History:
{chat_history}

Follow Up Question: {question}

Standalone Question:""",
    input_variables=["chat_history", "question"]
)

# Prompt for document summarization
LEGAL_SUMMARY_PROMPT = PromptTemplate(
    template="""Summarize the following legal document from Bangladesh law, focusing on key provisions, requirements, and implications.

Document:
{document}

Provide a concise summary that includes:
1. The main purpose of this law/section
2. Key provisions or requirements
3. Who is affected by this law
4. Important definitions or terms
5. Any penalties or consequences mentioned

Summary:""",
    input_variables=["document"]
)

# Prompt for comparing laws
LEGAL_COMPARISON_PROMPT = PromptTemplate(
    template="""Compare and contrast the following laws or legal provisions from Bangladesh:

Law/Provision 1:
{law1}

Law/Provision 2:
{law2}

Provide a comparison that includes:
1. Similarities between the laws
2. Key differences
3. Scope and applicability of each
4. Which law takes precedence (if applicable)
5. Practical implications of the differences

Comparison:""",
    input_variables=["law1", "law2"]
)

# Prompt for legal analysis
LEGAL_ANALYSIS_PROMPT = PromptTemplate(
    template="""Analyze the following legal scenario under Bangladesh law based on the provided context:

Legal Context:
{context}

Scenario:
{scenario}

Provide an analysis that includes:
1. Applicable laws and provisions
2. Legal interpretation
3. Potential outcomes or consequences
4. Relevant precedents or examples (if mentioned in context)
5. Recommendations or next steps

Legal Analysis:""",
    input_variables=["context", "scenario"]
)

# Prompt for Bengali language support
BENGALI_TRANSLATION_PROMPT = PromptTemplate(
    template="""You are assisting with Bangladesh law in both English and Bengali. The user has asked a question that may involve Bengali language content.

Context (may contain Bengali text):
{context}

Question: {question}

Instructions:
1. If the context contains Bengali text, provide translation where helpful
2. Answer in the same language as the question when possible
3. For legal terms, provide both English and Bengali versions
4. Ensure accuracy in legal terminology translation

Answer:""",
    input_variables=["context", "question"]
)

# Prompt for extracting specific information
LEGAL_EXTRACTION_PROMPT = PromptTemplate(
    template="""Extract specific information from the following Bangladesh law text based on the user's request.

Legal Text:
{context}

Information Requested: {query}

Extract and provide:
1. The specific information requested
2. The exact section or provision where it's found
3. Any related conditions or exceptions
4. Additional relevant details from the same section

Extracted Information:""",
    input_variables=["context", "query"]
)

# Prompt for generating legal explanations
LEGAL_EXPLANATION_PROMPT = PromptTemplate(
    template="""Explain the following legal concept or provision from Bangladesh law in simple terms that a non-lawyer can understand.

Legal Text:
{legal_text}

Provide an explanation that includes:
1. What this law means in everyday language
2. Real-world examples of how it applies
3. Why this law exists (if apparent from context)
4. What people need to know to comply with it
5. Common misconceptions to avoid

Explanation:""",
    input_variables=["legal_text"]
)

# System prompt for handling edge cases
FALLBACK_PROMPT = PromptTemplate(
    template="""I understand you're asking about Bangladesh law, but I need more specific information to provide an accurate answer.

Your question: {question}

Based on the available context, I cannot provide a complete answer. Here's what I can tell you:

{partial_context}

To better assist you, could you please:
1. Provide more specific details about your legal question
2. Specify which area of law you're interested in (criminal, civil, commercial, etc.)
3. Mention any specific acts or regulations you're referring to

How can I help you with Bangladesh law today?""",
    input_variables=["question", "partial_context"]
)


class PromptSelector:
    """Utility class to select appropriate prompts based on query type"""

    @staticmethod
    def select_prompt(query_type: str) -> PromptTemplate:
        """
        Select the appropriate prompt template based on query type

        Args:
            query_type: Type of query (qa, chat, summary, comparison, etc.)

        Returns:
            Appropriate PromptTemplate
        """
        prompt_mapping = {
            "qa": LEGAL_QA_PROMPT,
            "chat": LEGAL_CHAT_PROMPT,
            "condense": CONDENSE_QUESTION_PROMPT,
            "summary": LEGAL_SUMMARY_PROMPT,
            "comparison": LEGAL_COMPARISON_PROMPT,
            "analysis": LEGAL_ANALYSIS_PROMPT,
            "bengali": BENGALI_TRANSLATION_PROMPT,
            "extraction": LEGAL_EXTRACTION_PROMPT,
            "explanation": LEGAL_EXPLANATION_PROMPT,
            "fallback": FALLBACK_PROMPT
        }

        return prompt_mapping.get(query_type, LEGAL_QA_PROMPT)

    @staticmethod
    def detect_query_type(question: str) -> str:
        """
        Detect the type of query based on keywords and patterns

        Args:
            question: User's question

        Returns:
            Query type string
        """
        question_lower = question.lower()

        # Check for specific patterns
        if any(word in question_lower for word in ["compare", "difference", "versus", "vs"]):
            return "comparison"
        elif any(word in question_lower for word in ["summarize", "summary", "brief"]):
            return "summary"
        elif any(word in question_lower for word in ["analyze", "analysis", "evaluate"]):
            return "analysis"
        elif any(word in question_lower for word in ["explain", "what does", "meaning"]):
            return "explanation"
        elif any(word in question_lower for word in ["extract", "find", "specific"]):
            return "extraction"
        elif any(word in question_lower for word in ["bengali", "bangla", "বাংলা"]):
            return "bengali"
        else:
            return "qa"


# Export all prompts and utility class
__all__ = [
    'LEGAL_QA_PROMPT',
    'LEGAL_CHAT_PROMPT',
    'CONDENSE_QUESTION_PROMPT',
    'LEGAL_SUMMARY_PROMPT',
    'LEGAL_COMPARISON_PROMPT',
    'LEGAL_ANALYSIS_PROMPT',
    'BENGALI_TRANSLATION_PROMPT',
    'LEGAL_EXTRACTION_PROMPT',
    'LEGAL_EXPLANATION_PROMPT',
    'FALLBACK_PROMPT',
    'PromptSelector'
]