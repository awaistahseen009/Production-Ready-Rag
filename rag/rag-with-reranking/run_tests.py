import argparse
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from tqdm import tqdm

from evaluate import evaluate_all_answers, evaluate_all_retrieval, load_test_dataset

TEST_FILE = "test.jsonl"

def setup_logging(run_dir: Path):
    logger = logging.getLogger("eval")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)
    fh = logging.FileHandler(run_dir / "evaluation.log")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
    return logger

def evaluate_retrieval(logger):
    logger.info("Starting retrieval evaluation...")
    tests = load_test_dataset(TEST_FILE)
    total_mrr = total_ndcg = total_coverage = 0.0
    category_mrr = defaultdict(list)

    retrieval_iter = tqdm(evaluate_all_retrieval(), total=len(tests), desc="Retrieval", unit="test")

    for test, result, _ in retrieval_iter:
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_coverage += result.keyword_coverage
        category_mrr[test.category].append(result.mrr)

    count = len(tests)
    avg_mrr = total_mrr / count
    avg_ndcg = total_ndcg / count
    avg_coverage = total_coverage / count

    logger.info(f"Retrieval Evaluation Complete: {count} tests")
    logger.info(f"Overall MRR: {avg_mrr:.4f}")
    logger.info(f"Overall nDCG: {avg_ndcg:.4f}")
    logger.info(f"Overall Keyword Coverage: {avg_coverage:.1f}%")

    cat_data = []
    for cat, scores in category_mrr.items():
        avg = sum(scores) / len(scores)
        cat_data.append({"category": cat, "avg_mrr": avg})
        logger.info(f"Category '{cat}' MRR: {avg:.4f} (n={len(scores)})")

    return pd.DataFrame(cat_data), {
        "overall_mrr": avg_mrr,
        "overall_ndcg": avg_ndcg,
        "overall_coverage": avg_coverage,
        "total_tests": count,
    }

def evaluate_answers(logger):
    logger.info("Starting answer evaluation...")
    tests = load_test_dataset(TEST_FILE)
    
    # Totals for overall averages
    total_acc = total_comp = total_rel = total_faith = total_ctx_rel = total_ctx_util = total_unsupp = 0.0
    
    # Per-category tracking
    category_acc = defaultdict(list)
    category_comp = defaultdict(list)
    category_rel = defaultdict(list)
    category_faith = defaultdict(list)
    category_ctx_rel = defaultdict(list)
    category_ctx_util = defaultdict(list)
    category_unsupp = defaultdict(list)

    answer_iter = tqdm(evaluate_all_answers(), total=len(tests), desc="Answers  ", unit="test")

    for test, result, _ in answer_iter:
        total_acc += result.accuracy
        total_comp += result.completeness
        total_rel += result.relevance
        total_faith += result.faithfulness
        total_ctx_rel += result.context_relevance
        total_ctx_util += result.context_utilization
        total_unsupp += result.unsupported_claims

        cat = test.category
        category_acc[cat].append(result.accuracy)
        category_comp[cat].append(result.completeness)
        category_rel[cat].append(result.relevance)
        category_faith[cat].append(result.faithfulness)
        category_ctx_rel[cat].append(result.context_relevance)
        category_ctx_util[cat].append(result.context_utilization)
        category_unsupp[cat].append(result.unsupported_claims)

    count = len(tests)
    avg_acc = total_acc / count
    avg_comp = total_comp / count
    avg_rel = total_rel / count
    avg_faith = total_faith / count
    avg_ctx_rel = total_ctx_rel / count
    avg_ctx_util = total_ctx_util / count
    avg_unsupp = total_unsupp / count

    logger.info(f"Answer Evaluation Complete: {count} tests")
    logger.info(f"Overall Accuracy: {avg_acc:.3f}/5")
    logger.info(f"Overall Completeness: {avg_comp:.3f}/5")
    logger.info(f"Overall Relevance: {avg_rel:.3f}/5")
    logger.info(f"Overall Faithfulness: {avg_faith:.3f}/5")
    logger.info(f"Overall Context Relevance: {avg_ctx_rel:.3f}/5")
    logger.info(f"Overall Context Utilization: {avg_ctx_util:.3f}/5")
    logger.info(f"Overall Unsupported Claims (avg): {avg_unsupp:.2f}")

    # Per-category logging
    for cat in category_acc:
        n = len(category_acc[cat])
        logger.info(f"Category '{cat}' Accuracy: {sum(category_acc[cat])/n:.3f}/5 (n={n})")
        logger.info(f"Category '{cat}' Completeness: {sum(category_comp[cat])/n:.3f}/5")
        logger.info(f"Category '{cat}' Relevance: {sum(category_rel[cat])/n:.3f}/5")
        logger.info(f"Category '{cat}' Faithfulness: {sum(category_faith[cat])/n:.3f}/5")
        logger.info(f"Category '{cat}' Context Relevance: {sum(category_ctx_rel[cat])/n:.3f}/5")
        logger.info(f"Category '{cat}' Context Utilization: {sum(category_ctx_util[cat])/n:.3f}/5")
        logger.info(f"Category '{cat}' Avg Unsupported Claims: {sum(category_unsupp[cat])/n:.2f}")

    # Build DataFrame with all per-category averages
    cat_data = []
    categories = set(category_acc.keys())
    for cat in categories:
        n = len(category_acc[cat])
        cat_data.append({
            "category": cat,
            "avg_accuracy": sum(category_acc[cat]) / n,
            "avg_completeness": sum(category_comp[cat]) / n,
            "avg_relevance": sum(category_rel[cat]) / n,
            "avg_faithfulness": sum(category_faith[cat]) / n,
            "avg_context_relevance": sum(category_ctx_rel[cat]) / n,
            "avg_context_utilization": sum(category_ctx_util[cat]) / n,
            "avg_unsupported_claims": sum(category_unsupp[cat]) / n,
        })

    return pd.DataFrame(cat_data), {
        "overall_accuracy": avg_acc,
        "overall_completeness": avg_comp,
        "overall_relevance": avg_rel,
        "overall_faithfulness": avg_faith,
        "overall_context_relevance": avg_ctx_rel,
        "overall_context_utilization": avg_ctx_util,
        "overall_unsupported_claims": avg_unsupp,
        "total_tests": count,
    }

def save_plots_retrieval(df: pd.DataFrame, run_dir: Path):
    retrieval_dir = run_dir / "retrieval"
    retrieval_dir.mkdir(parents=True, exist_ok=True)
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#DDA0DD', '#98D8C8', '#F7DC6F', '#FF9FF3', '#54A0FF']
    
    fig_px = px.bar(
        df.sort_values("avg_mrr", ascending=False),
        x="category",
        y="avg_mrr",
        title="Average MRR by Category",
        labels={"avg_mrr": "Average MRR", "category": "Category"},
        color="avg_mrr",
        color_continuous_scale=["red", "orange", "green"],
    )
    fig_px.update_layout(yaxis_range=[0, 1])
    fig_px.write_html(retrieval_dir / "mrr_by_category_plotly.html")

    plt.figure(figsize=(12, 6))
    bars = plt.bar(df["category"], df["avg_mrr"], color=colors[:len(df)], edgecolor="black")
    plt.title("Average MRR by Category")
    plt.ylabel("Average MRR")
    plt.ylim(0, 1)
    plt.xticks(rotation=45, ha="right")
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.1%}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(retrieval_dir / "mrr_by_category_matplotlib.png")
    plt.savefig(retrieval_dir / "mrr_by_category_matplotlib.pdf")
    plt.close()

def save_plots_answers(df: pd.DataFrame, run_dir: Path):
    answers_dir = run_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#DDA0DD', '#98D8C8', '#F7DC6F', '#FF9FF3', '#54A0FF']
    
    # Only plot the main 1-5 scale metrics
    metrics = ["avg_accuracy", "avg_completeness", "avg_relevance", "avg_faithfulness",
               "avg_context_relevance", "avg_context_utilization"]
    
    for metric in metrics:
        label = metric.replace("avg_", "").replace("_", " ").title()
        fig_px = px.bar(
            df.sort_values(metric, ascending=False),
            x="category",
            y=metric,
            title=f"Average {label} by Category",
            labels={metric: f"Average {label} (1-5)", "category": "Category"},
            color=metric,
            color_continuous_scale=["red", "orange", "green"],
        )
        fig_px.update_layout(yaxis_range=[1, 5])
        fig_px.write_html(answers_dir / f"{metric}_by_category_plotly.html")

        plt.figure(figsize=(12, 6))
        bars = plt.bar(df["category"], df[metric], color=colors[:len(df)], edgecolor="black")
        plt.title(f"Average {label} by Category")
        plt.ylabel(f"Average {label} (1-5)")
        plt.ylim(1, 5)
        plt.xticks(rotation=45, ha="right")
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                     f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(answers_dir / f"{metric}_by_category_matplotlib.png")
        plt.savefig(answers_dir / f"{metric}_by_category_matplotlib.pdf")
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation and save results + graphs")
    parser.add_argument("--run_name", type=str, required=True, help="Name of this run (used for output folder)")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    parent_dir = Path(__file__).parent.parent
    run_dir = parent_dir / "evaluation_results" / f"{args.run_name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logging(run_dir)

    logger.info(f"Starting evaluation run: {args.run_name}")
    logger.info(f"Results will be saved to: {run_dir}")

    retrieval_df, retrieval_summary = evaluate_retrieval(logger)
    retrieval_dir = run_dir / "retrieval"
    retrieval_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([retrieval_summary]).to_csv(retrieval_dir / "summary.csv", index=False)
    retrieval_df.to_csv(retrieval_dir / "per_category.csv", index=False)
    save_plots_retrieval(retrieval_df, run_dir)

    answer_df, answer_summary = evaluate_answers(logger)
    answers_dir = run_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([answer_summary]).to_csv(answers_dir / "summary.csv", index=False)
    answer_df.to_csv(answers_dir / "per_category.csv", index=False)
    save_plots_answers(answer_df, run_dir)

    logger.info("All evaluations completed!")
    logger.info(f"All results and graphs saved in: {run_dir}")

if __name__ == "__main__":
    main()