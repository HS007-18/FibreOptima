import os
import pytest
from src.agent.rag_indexer import KnowledgeIndexer
from src.agent.investigator import InvestigationAgent
from src.schema.intelligence import AnomalyIntelligencePacket


def test_knowledge_indexer(tmp_path):
    # Create temporary doc
    doc_dir = tmp_path / "raw"
    doc_dir.mkdir()
    doc_file = doc_dir / "test_doc.md"
    doc_file.write_text(
        "---\nSource: Test Source\n---\nTextile loom vibrating at speed above 250 rpm generates micro tears.",
        encoding="utf-8",
    )

    chroma_dir = tmp_path / "chroma_db"
    indexer = KnowledgeIndexer(persist_directory=str(chroma_dir))
    indexer.index_directory(str(doc_dir))

    # Test retrieval
    agent = InvestigationAgent(persist_directory=str(chroma_dir))
    packet = AnomalyIntelligencePacket(
        record_id="TEST-1",
        is_anomalous=True,
        anomaly_score=-0.1,
        business_rule_flag=True,
        ml_anomaly_flag=True,
        risk_class="High Risk",
        observed_telemetry={"Fabric type": "Cotton", "Production speed": 300, "Waste percentage": 20.0},
        statistical_deviations={},
        feature_contributions={},
    )

    queries, knowledge_str = agent.retrieve_evidence(packet)
    assert len(queries) > 0
    assert "vibrating" in knowledge_str or "Test Source" in knowledge_str or "matching" in knowledge_str
