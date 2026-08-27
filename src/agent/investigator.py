import os
import json
import logging
from typing import List, Tuple, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.schema.intelligence import AnomalyIntelligencePacket

logger = logging.getLogger(__name__)


class InvestigationAgent:
    """Agent for investigating textile waste anomalies using RAG evidence."""

    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        llm_base_url: str = None,
        llm_api_key: str = None,
    ):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = Chroma(
            collection_name="textile_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

        # Resolve LLM configuration
        api_key = (
            llm_api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("LLM_API_KEY")
        )
        base_url = (
            llm_base_url
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("LLM_BASE_URL")
        )

        self.llm_available = bool(api_key and api_key != "not-needed")
        if self.llm_available:
            try:
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    base_url=base_url,
                    api_key=api_key,
                    temperature=0.0,
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatOpenAI: {e}")
                self.llm_available = False
                self.llm = None
        else:
            self.llm = None

        self.query_generation_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a textile AI diagnostician. Generate 2 to 4 queries to retrieve maintenance docs based on the telemetry. Output ONLY queries separated by newlines.",
                ),
                (
                    "user",
                    "Telemetry: {telemetry}\nML Feature Contributions: {contributions}",
                ),
            ]
        )

        self.investigation_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Format response exactly:\nInvestigation Mode: LLM Agent\n\n1. OBSERVED EVIDENCE\n2. ML EVIDENCE\n3. RETRIEVED KNOWLEDGE\n4. LOGICAL INFERENCE\nDo not fabricate knowledge.",
                ),
                (
                    "user",
                    "--- PACKET DATA ---\nRecord ID: {record_id}\nRisk Class: {risk_class}\nBusiness Rule Violated: {biz_flag}\nML Anomaly Flag: {ml_flag}\nAnomaly Score: {anomaly_score}\nTelemetry:\n{telemetry}\nZ-Scores:\n{z_scores}\nContributions:\n{contributions}\n--- RETRIEVED KNOWLEDGE ---\n{retrieved_knowledge}",
                ),
            ]
        )

    def _generate_fallback_queries(self, packet: AnomalyIntelligencePacket) -> List[str]:
        """Deterministic query generator from telemetry signals."""
        queries = []
        fabric = packet.observed_telemetry.get("Fabric type", "Textile")
        waste_pct = packet.observed_telemetry.get("Waste percentage", 0.0)

        queries.append(f"{fabric} waste percentage abnormal operational speed")
        if packet.observed_telemetry.get("Machine age", 0) > 10:
            queries.append("Machine age exceeding 10 years speed rpm vibration waste")
        if packet.observed_telemetry.get("Humidity") is None or pd_isna(packet.observed_telemetry.get("Humidity")):
            queries.append("Missing humidity sensor failure dry cotton wool waste")
        if waste_pct > 15:
            queries.append("High waste percentage loom inspection threshold")

        return queries

    def retrieve_evidence(self, packet: AnomalyIntelligencePacket) -> Tuple[List[str], str]:
        """Retrieve relevant textile domain evidence chunks from Chroma vector store."""
        queries = []
        if self.llm_available:
            try:
                telemetry_str = json.dumps(packet.observed_telemetry)
                contribs_str = json.dumps(packet.feature_contributions)
                query_response = self.llm.invoke(
                    self.query_generation_prompt.format_messages(
                        telemetry=telemetry_str, contributions=contribs_str
                    )
                )
                queries = [q.strip() for q in query_response.content.split("\n") if q.strip()]
            except Exception as e:
                logger.warning(f"LLM query generation failed, using fallback: {e}")

        if not queries:
            queries = self._generate_fallback_queries(packet)

        retrieved_docs = {}
        for query in queries:
            try:
                docs = self.vector_store.similarity_search(query, k=2)
                for doc in docs:
                    if doc.page_content not in retrieved_docs:
                        retrieved_docs[doc.page_content] = doc
            except Exception as e:
                logger.warning(f"Vector search failed for query '{query}': {e}")

        knowledge_texts = []
        for content, doc in retrieved_docs.items():
            source = doc.metadata.get("Source", "Textile Mill Handbook")
            knowledge_texts.append(f"[Source: {source}]\n{content}\n")

        retrieved_knowledge_str = (
            "\n".join(knowledge_texts) if knowledge_texts else "No matching domain evidence found in knowledge base."
        )
        return queries, retrieved_knowledge_str

    def investigate(self, packet: AnomalyIntelligencePacket) -> str:
        """Run investigation in LLM Agent mode or Offline Evidence Engine mode."""
        queries, retrieved_knowledge_str = self.retrieve_evidence(packet)
        telemetry_str = json.dumps(packet.observed_telemetry, indent=2)
        contribs_str = json.dumps(packet.feature_contributions, indent=2)
        z_scores_str = json.dumps(packet.statistical_deviations, indent=2)

        if self.llm_available:
            try:
                packet.investigation_mode = "LLM Agent"
                final_report = self.llm.invoke(
                    self.investigation_prompt.format_messages(
                        record_id=packet.record_id,
                        risk_class=packet.risk_class,
                        biz_flag=packet.business_rule_flag,
                        ml_flag=packet.ml_anomaly_flag,
                        anomaly_score=packet.anomaly_score,
                        telemetry=telemetry_str,
                        z_scores=z_scores_str,
                        contributions=contribs_str,
                        retrieved_knowledge=retrieved_knowledge_str,
                    )
                )
                return final_report.content
            except Exception as e:
                logger.warning(f"LLM investigation call failed, defaulting to Offline Evidence Engine: {e}")

        # Deterministic Offline Evidence Engine Synthesis
        packet.investigation_mode = "Offline Evidence Engine"
        report_lines = [
            "Investigation Mode: Offline Evidence Engine",
            "--------------------------------------------------",
            "1. OBSERVED EVIDENCE",
            f"- Record / Batch ID: {packet.record_id}",
            f"- Observed Telemetry: {telemetry_str}",
            f"- Calculated Waste Percentage: {packet.observed_telemetry.get('Waste percentage', 0.0):.2f}%",
            "",
            "2. ML & OPERATIONAL EVIDENCE",
            f"- Risk Classification: {packet.risk_class}",
            f"- Isolation Forest Anomaly Score: {packet.anomaly_score:.4f}",
            f"- ML Statistical Anomaly Flag: {'POSITIVE' if packet.ml_anomaly_flag else 'NEGATIVE'}",
            f"- Business Rule Violation Flag: {'POSITIVE' if packet.business_rule_flag else 'NEGATIVE'}",
            f"- Top Feature Contributions: {contribs_str}",
            "",
            "3. RETRIEVED DOMAIN KNOWLEDGE EVIDENCE",
            retrieved_knowledge_str,
            "",
            "4. LOGICAL INFERENCE & ACTIONABLE RECOMMENDATIONS",
        ]

        if packet.risk_class == "High Risk":
            report_lines.append(
                "- CRITICAL RISK: Machine strain/speed exceeds operational thresholds causing severe waste."
            )
            report_lines.append("- ACTION: Halt production line immediately, verify loom calibration and humidity control.")
        elif packet.risk_class == "Warning":
            report_lines.append(
                "- MODERATE RISK: Operational parameters deviate from baseline. Inspect machine load and speed."
            )
            report_lines.append("- ACTION: Schedule maintenance review and check environmental sensors.")
        else:
            report_lines.append("- NORMAL OPERATIONS: Telemetry aligns with baseline operational parameters.")

        return "\n".join(report_lines)


def pd_isna(val):
    import pandas as pd
    return pd.isna(val)
