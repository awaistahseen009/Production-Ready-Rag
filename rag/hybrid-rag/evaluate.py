import sys
import math
from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv

from test import Test, load_test_dataset
from answer import answer_question, fetch_context


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
db_name = "vector_db"


class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""

    mrr: float = Field(description="Mean Reciprocal Rank - average across all keywords")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(description="Number of keywords found in top-k results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")


class AnswerEval(BaseModel):
    feedback: str

    accuracy: float = Field(
        description="Factual correctness vs reference answer. 1 (wrong) to 5 (perfect)."
    )

    completeness: float = Field(
        description="Coverage of all required information from reference answer. 1 to 5."
    )

    relevance: float = Field(
        description="How directly the answer addresses the question without extra info. 1 to 5."
    )

    faithfulness: float = Field(
        description="Are all claims in the answer supported by the retrieved context? 1 (hallucinated) to 5 (fully grounded)."
    )

    context_relevance: float = Field(
        description="How relevant is the retrieved context to the question? 1 (irrelevant) to 5 (highly relevant)."
    )

    context_utilization: float = Field(
        description="Did the answer meaningfully use the retrieved context? 1 (ignored context) to 5 (fully utilized)."
    )

    unsupported_claims: int = Field(
        description="Number of claims in the answer that are NOT supported by the retrieved context."
    )

def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    """Calculate reciprocal rank for a single keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    """Calculate Discounted Cumulative Gain."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)  # i+2 because rank starts at 1
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    """Calculate nDCG for a single keyword (binary relevance, case-insensitive)."""
    keyword_lower = keyword.lower()

    # Binary relevance: 1 if keyword found, 0 otherwise
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0 for doc in retrieved_docs[:k]
    ]

    # DCG
    dcg = calculate_dcg(relevances, k)

    # Ideal DCG (best case: keyword in first position)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)

    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval(test: Test, k: int = 10) -> RetrievalEval:
    """
    Evaluate retrieval performance for a test question.

    Args:
        test: Test object containing question and keywords
        k: Number of top documents to retrieve (default 10)

    Returns:
        RetrievalEval object with MRR, nDCG, and keyword coverage metrics
    """
    # Retrieve documents using shared answer module
    # This is changed here from vanilla rag and its combination of bm25(elastic search) and normal dense semantic search
    retrieved_docs = fetch_context(test.question)

    # Calculate MRR (average across all keywords)
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    # Calculate nDCG (average across all keywords)
    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    # Calculate keyword coverage
    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )
def evaluate_answer(test: Test) -> tuple[AnswerEval, str, list]:
    generated_answer, retrieved_docs = answer_question(test.question)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert RAG evaluator. Your job is to judge not only correctness, "
                "but also grounding and faithfulness. Be strict. Do NOT reward fluent hallucinations."
            ),
        },
        {
            "role": "user",
            "content": f"""
Question:
{test.question}

Retrieved Context:
{chr(10).join([doc.page_content for doc in retrieved_docs])}

Generated Answer:
{generated_answer}

Reference Answer:
{test.reference_answer}

Evaluate the generated answer using the following criteria:

1. Accuracy (1–5): Compare against the reference answer.
2. Completeness (1–5): Coverage of all required information.
3. Relevance (1–5): Directness without extra info.
4. Faithfulness (1–5): All claims supported by context.
5. Context Relevance (1–5): Relevance of retrieved context.
6. Context Utilization (1–5): Use of retrieved context.
7. Unsupported Claims (integer): Count of unsupported claims.

Provide concise feedback and strict numeric scores. Output ONLY valid JSON matching the required schema.
"""
        },
    ]

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            judge_response = completion(
                model=MODEL,
                messages=judge_messages,
                response_format=AnswerEval,
                temperature=0.0,
            )
            content = judge_response.choices[0].message.content.strip()
            answer_eval = AnswerEval.model_validate_json(content)
            return answer_eval, generated_answer, retrieved_docs
        except Exception as e:
            if attempt == max_retries:
                raise RuntimeError(f"Failed to parse judge response after {max_retries + 1} attempts: {e}")
            # Optional: add small delay or log retry
            continue

    # Unreachable, but keeps type checker happy
    raise RuntimeError("Unexpected error in evaluate_answer")

# def evaluate_answer(test: Test) -> tuple[AnswerEval, str, list]:
#     """
#     Evaluate answer quality using LLM-as-a-judge (async).

#     Args:
#         test: Test object containing question and reference answer

#     Returns:
#         Tuple of (AnswerEval object, generated_answer string, retrieved_docs list)
#     """
#     # Get RAG response using shared answer module
#     generated_answer, retrieved_docs = answer_question(test.question)

#     # LLM judge prompt
#     judge_messages = [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are an expert RAG evaluator. Your job is to judge not only correctness, "
#                     "but also grounding and faithfulness. Be strict. Do NOT reward fluent hallucinations."
#                 ),
#             },
#             {
#                 "role": "user",
#                 "content": f"""
#         Question:
#         {test.question}

#         Retrieved Context:
#         {chr(10).join([doc.page_content for doc in retrieved_docs])}

#         Generated Answer:
#         {generated_answer}

#         Reference Answer:
#         {test.reference_answer}

#         Evaluate the generated answer using the following criteria:

#         1. Accuracy (1–5):
#         Compare against the reference answer. Any incorrect factual claim must reduce the score.

#         2. Completeness (1–5):
#         Check whether ALL information from the reference answer is covered.

#         3. Relevance (1–5):
#         Check whether the answer directly addresses the question without adding extra information.

#         4. Faithfulness (1–5):
#         Check whether EVERY claim in the answer is supported by the retrieved context.
#         If the answer contains hallucinated or unsupported claims, reduce this score.

#         5. Context Relevance (1–5):
#         Judge how relevant the retrieved context is to the question.

#         6. Context Utilization (1–5):
#         Judge whether the answer actually uses the retrieved context or ignores it.

#         7. Unsupported Claims (integer):
#         Count the number of claims in the answer that are NOT supported by the retrieved context.

#         Provide:
#         - Concise feedback
#         - Strict numeric scores
#         - Be conservative: only give 5/5 if truly perfect.
#         """
#             },
#         ]


#     # Call LLM judge with structured outputs (async)
#     judge_response = completion(model=MODEL, messages=judge_messages, response_format=AnswerEval)

#     answer_eval = AnswerEval.model_validate_json(judge_response.choices[0].message.content)

#     return answer_eval, generated_answer, retrieved_docs


def evaluate_all_retrieval():
    """Evaluate all retrieval tests."""
    tests = load_test_dataset()
    total_tests = len(tests)
    for index, test in enumerate(tests):
        result = evaluate_retrieval(test)
        progress = (index + 1) / total_tests
        yield test, result, progress


def evaluate_all_answers():
    """Evaluate all answers to tests using batched async execution."""
    tests = load_test_dataset()
    total_tests = len(tests)
    for index, test in enumerate(tests):
        result = evaluate_answer(test)[0]
        progress = (index + 1) / total_tests
        yield test, result, progress


def run_cli_evaluation(test_number: int):
    """Run evaluation for a specific test (async helper for CLI)."""
    # Load tests
    tests = load_test_dataset("test.jsonl")

    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test_row_number must be between 0 and {len(tests) - 1}")
        sys.exit(1)

    # Get the test
    test = tests[test_number]

    # Print test info
    print(f"\n{'=' * 80}")
    print(f"Test #{test_number}")
    print(f"{'=' * 80}")
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Category: {test.category}")
    print(f"Reference Answer: {test.reference_answer}")

    # Retrieval Evaluation
    print(f"\n{'=' * 80}")
    print("Retrieval Evaluation")
    print(f"{'=' * 80}")

    retrieval_result = evaluate_retrieval(test)

    print(f"MRR: {retrieval_result.mrr:.4f}")
    print(f"nDCG: {retrieval_result.ndcg:.4f}")
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")

    # Answer Evaluation
    print(f"\n{'=' * 80}")
    print("Answer Evaluation")
    print(f"{'=' * 80}")

    answer_result, generated_answer, retrieved_docs = evaluate_answer(test)

    print(f"\nGenerated Answer:\n{generated_answer}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance: {answer_result.relevance:.2f}/5")
    print(f"\n{'=' * 80}\n")


def main():
    """CLI to evaluate a specific test by row number."""
    if len(sys.argv) != 2:
        print("Usage: uv run eval.py <test_row_number>")
        sys.exit(1)

    try:
        test_number = int(sys.argv[1])
    except ValueError:
        print("Error: test_row_number must be an integer")
        sys.exit(1)

    run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()