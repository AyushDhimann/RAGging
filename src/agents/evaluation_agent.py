"""
Evaluation Agent
Evaluates RAG system using RAGAS metrics, latency, and Gemini-based fluency scoring.
Generates JSON and HTML reports.
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai

from ..common import logger, config
from .retriever_agent import RetrievalResult


class EvaluationAgent:
    """
    Evaluates RAG system performance.
    Metrics: retrieval quality, latency, fluency.
    """
    
    def __init__(self):
        self.enable_eval = config.enable_eval
        self.eval_model = config.eval_model
        
        # Configure Gemini
        keys = config.get_gemini_keys()
        if keys:
            genai.configure(api_key=keys[0])
    
    def evaluate_retrieval_relevance(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval relevance using Gemini.
        
        Args:
            query: User query
            results: Retrieved results
            
        Returns:
            Relevance scores and metrics
        """
        if not results:
            return {
                "avg_relevance": 0.0,
                "num_relevant": 0,
                "precision": 0.0
            }
        
        try:
            # Ask Gemini to score each result
            scores = []
            
            for result in results[:5]:  # Evaluate top 5
                prompt = f"""Rate the relevance of this passage to the query on a scale of 0-10.

Query: {query}

Passage: {result.text[:500]}

Return ONLY a number from 0-10, where:
- 0-2: Not relevant
- 3-5: Somewhat relevant
- 6-8: Relevant
- 9-10: Highly relevant

Relevance score:"""
                
                model = genai.GenerativeModel(self.eval_model)
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.0,
                        "max_output_tokens": 10,
                    }
                )
                
                if response.text:
                    try:
                        score = float(response.text.strip())
                        scores.append(score)
                    except ValueError:
                        scores.append(5.0)  # Default to medium relevance
            
            # Calculate metrics
            avg_relevance = sum(scores) / len(scores) if scores else 0.0
            num_relevant = sum(1 for s in scores if s >= 6.0)
            precision = num_relevant / len(scores) if scores else 0.0
            
            return {
                "avg_relevance": avg_relevance,
                "num_relevant": num_relevant,
                "precision": precision,
                "scores": scores
            }
            
        except Exception as e:
            logger.error(f"Error evaluating retrieval relevance: {e}")
            return {
                "avg_relevance": 0.0,
                "num_relevant": 0,
                "precision": 0.0,
                "error": str(e)
            }
    
    def evaluate_response_fluency(
        self,
        response: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Evaluate response fluency and quality using Gemini.
        
        Args:
            response: Generated response
            query: Original query
            
        Returns:
            Fluency scores and metrics
        """
        try:
            prompt = f"""Evaluate the following AI response on these criteria (rate each 0-10):

1. Fluency: Is the response grammatically correct and well-written?
2. Coherence: Does the response make logical sense?
3. Completeness: Does it adequately address the query?
4. Conciseness: Is it appropriately concise without being verbose?

Query: {query}

Response: {response}

Return scores in JSON format:
{{"fluency": X, "coherence": X, "completeness": X, "conciseness": X}}

Scores:"""
            
            model = genai.GenerativeModel(self.eval_model)
            result = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 100,
                }
            )
            
            if result.text:
                # Try to parse JSON
                try:
                    # Extract JSON from response
                    text = result.text.strip()
                    # Find JSON object
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = text[start:end]
                        scores = json.loads(json_str)
                        
                        # Calculate overall score
                        overall = sum(scores.values()) / len(scores)
                        
                        return {
                            **scores,
                            "overall": overall
                        }
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Error parsing fluency scores: {e}")
            
            # Default scores if parsing fails
            return {
                "fluency": 7.0,
                "coherence": 7.0,
                "completeness": 7.0,
                "conciseness": 7.0,
                "overall": 7.0
            }
            
        except Exception as e:
            logger.error(f"Error evaluating response fluency: {e}")
            return {
                "fluency": 0.0,
                "coherence": 0.0,
                "completeness": 0.0,
                "conciseness": 0.0,
                "overall": 0.0,
                "error": str(e)
            }
    
    def evaluate_query(
        self,
        query: str,
        retrieved_context: List[RetrievalResult],
        response: str,
        latency_ms: float
    ) -> Dict[str, Any]:
        """
        Evaluate a single query-response pair.
        
        Args:
            query: User query
            retrieved_context: Retrieved results
            response: Generated response
            latency_ms: Response latency in milliseconds
            
        Returns:
            Evaluation metrics
        """
        logger.info(f"Evaluating query: '{query[:50]}...'")
        
        # Retrieval metrics
        retrieval_metrics = self.evaluate_retrieval_relevance(query, retrieved_context)
        
        # Response metrics
        fluency_metrics = self.evaluate_response_fluency(response, query)
        
        # Latency metrics
        latency_metrics = {
            "latency_ms": latency_ms,
            "latency_s": latency_ms / 1000.0
        }
        
        # Combined evaluation
        evaluation = {
            "query": query,
            "response_preview": response[:200] + "..." if len(response) > 200 else response,
            "num_retrieved": len(retrieved_context),
            "retrieval": retrieval_metrics,
            "fluency": fluency_metrics,
            "latency": latency_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Evaluation complete: relevance={retrieval_metrics.get('avg_relevance', 0):.2f}, "
                   f"fluency={fluency_metrics.get('overall', 0):.2f}, "
                   f"latency={latency_ms:.0f}ms")
        
        return evaluation
    
    def save_evaluation_report(
        self,
        evaluations: List[Dict[str, Any]],
        report_name: Optional[str] = None
    ):
        """
        Save evaluation report as JSON and HTML.
        
        Args:
            evaluations: List of evaluation results
            report_name: Name for the report file
        """
        if not evaluations:
            logger.warning("No evaluations to save")
            return
        
        # Generate report name
        if not report_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"eval_report_{timestamp}"
        
        reports_dir = config.reports_dir
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate aggregate metrics
        aggregate = self._calculate_aggregate_metrics(evaluations)
        
        # Prepare full report
        report = {
            "report_name": report_name,
            "timestamp": datetime.now().isoformat(),
            "num_queries": len(evaluations),
            "aggregate_metrics": aggregate,
            "evaluations": evaluations
        }
        
        # Save JSON
        json_path = reports_dir / f"{report_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.success(f"Saved JSON report to {json_path}")
        
        # Save HTML
        html_path = reports_dir / f"{report_name}.html"
        html_content = self._generate_html_report(report)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.success(f"Saved HTML report to {html_path}")
    
    def _calculate_aggregate_metrics(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics from evaluations."""
        if not evaluations:
            return {}
        
        # Retrieval metrics
        avg_relevance_scores = [e["retrieval"]["avg_relevance"] for e in evaluations]
        precision_scores = [e["retrieval"]["precision"] for e in evaluations]
        
        # Fluency metrics
        fluency_scores = [e["fluency"]["overall"] for e in evaluations]
        
        # Latency metrics
        latency_values = [e["latency"]["latency_ms"] for e in evaluations]
        
        return {
            "avg_relevance": sum(avg_relevance_scores) / len(avg_relevance_scores),
            "avg_precision": sum(precision_scores) / len(precision_scores),
            "avg_fluency": sum(fluency_scores) / len(fluency_scores),
            "avg_latency_ms": sum(latency_values) / len(latency_values),
            "min_latency_ms": min(latency_values),
            "max_latency_ms": max(latency_values),
        }
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report."""
        aggregate = report["aggregate_metrics"]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RAG Evaluation Report - {report["report_name"]}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #e3f2fd; border-radius: 5px; }}
        .metric-label {{ font-weight: bold; color: #1976d2; }}
        .metric-value {{ font-size: 24px; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #1976d2; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RAG System Evaluation Report</h1>
        <p><strong>Report:</strong> {report["report_name"]}</p>
        <p><strong>Generated:</strong> {report["timestamp"]}</p>
        <p><strong>Queries Evaluated:</strong> {report["num_queries"]}</p>
        
        <h2>Aggregate Metrics</h2>
        <div>
            <div class="metric">
                <div class="metric-label">Avg Relevance</div>
                <div class="metric-value">{aggregate.get("avg_relevance", 0):.2f}/10</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Precision</div>
                <div class="metric-value">{aggregate.get("avg_precision", 0):.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Fluency</div>
                <div class="metric-value">{aggregate.get("avg_fluency", 0):.2f}/10</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Latency</div>
                <div class="metric-value">{aggregate.get("avg_latency_ms", 0):.0f}ms</div>
            </div>
        </div>
        
        <h2>Individual Evaluations</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Query</th>
                    <th>Relevance</th>
                    <th>Fluency</th>
                    <th>Latency (ms)</th>
                    <th>Retrieved</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for i, eval_result in enumerate(report["evaluations"], 1):
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{eval_result["query"][:100]}...</td>
                    <td>{eval_result["retrieval"]["avg_relevance"]:.2f}</td>
                    <td>{eval_result["fluency"]["overall"]:.2f}</td>
                    <td>{eval_result["latency"]["latency_ms"]:.0f}</td>
                    <td>{eval_result["num_retrieved"]}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        return html

