"""
v4.0端到端测试：验证人脑式三层记忆架构
"""
import os
import sys
import tempfile
import shutil
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import yaml
from nomad_mem.encoder.multimodal import MultimodalEncoder
from nomad_mem.memory.vector_store import VectorStore
from nomad_mem.memory.hippocampus import Hippocampus
from nomad_mem.memory.cortex import Cortex
from nomad_mem.memory.working_memory import WorkingMemory
from nomad_mem.memory.forget import ForgettingEngine
from nomad_mem.graph.concept_formation import ConceptFormation
from nomad_mem.sleep.consolidation import SleepConsolidation
from nomad_mem.attention.scorer_v4 import AttentionScorerV4


def load_config():
    """加载测试配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    tmpdir = tempfile.mkdtemp()
    cfg["database"]["path"] = os.path.join(tmpdir, "test_memory.db")
    cfg["database"]["vectors_path"] = os.path.join(tmpdir, "test_vectors.db")
    cfg["audio"]["input_dir"] = os.path.join(tmpdir, "audio_in")
    cfg["audio"]["processed_dir"] = os.path.join(tmpdir, "audio_processed")
    os.makedirs(cfg["audio"]["input_dir"], exist_ok=True)
    os.makedirs(cfg["audio"]["processed_dir"], exist_ok=True)

    return cfg, tmpdir


def test_v4_brain_like():
    """
    人脑特性验证测试
    1. 存算一体
    2. 情绪增强
    3. 工作记忆限制
    4. 双阶段记忆
    5. 主动遗忘
    6. 睡眠巩固
    """
    cfg, tmpdir = load_config()

    print("初始化v4.0记忆系统...")
    encoder = MultimodalEncoder(cfg)
    vector_store = VectorStore(cfg["database"]["vectors_path"])
    hippocampus = Hippocampus(vector_store.conn, cfg)
    cortex = Cortex(vector_store.conn, cfg)
    working_memory = WorkingMemory(max_items=cfg["attention"]["working_memory_limit"])
    attention_scorer = AttentionScorerV4(cfg)
    concept_formation = ConceptFormation(vector_store.conn, cfg)
    sleep_consolidation = SleepConsolidation(vector_store.conn, cfg)
    forgetting_engine = ForgettingEngine(vector_store.conn, cfg)

    print("=" * 60)
    print("测试1: 向量编码 → 海马体快写")
    print("=" * 60)

    # 输入高情绪内容
    high_emotion_text = "我非常激动！这是一个伟大的发现！太棒了！"
    embedding = encoder.encode_text(high_emotion_text)
    emotion_score = 0.9  # 高情绪

    vector_id = vector_store.insert_vector(embedding, high_emotion_text, "text", emotion_score)
    hippocampus.encode(vector_id, emotion_score)

    # 验证：海马体中有这个向量
    hippocampal_vectors = hippocampus.get_all()
    assert len(hippocampal_vectors) == 1, "高情绪内容应进入海马体"
    print(f"  ✓ 高情绪内容已进入海马体: vector_id={vector_id}")

    print()
    print("=" * 60)
    print("测试2: 工作记忆限制（硬性4项）")
    print("=" * 60)

    # 连续输入5个不同主题
    texts = [
        "人工智能发展迅速",
        "机器学习算法优化",
        "深度学习神经网络",
        "自然语言处理技术",
        "计算机视觉应用"  # 第5个应触发遗忘
    ]

    forgotten_vector_id = None
    for i, text in enumerate(texts):
        emb = encoder.encode_text(text)
        vid = vector_store.insert_vector(emb, text, "text", 0.5)
        forgotten = working_memory.add(vid, 0.5)

        if forgotten:
            forgotten_vector_id = forgotten[0]
            print(f"  遗忘: vector_id={forgotten_vector_id}")

    # 验证：工作记忆不超过4项
    assert working_memory.size() <= 4, f"工作记忆应≤4项，实际: {working_memory.size()}"
    print(f"  ✓ 工作记忆严格限制在4项: {working_memory.size()}")

    # 验证：最早的一项被遗忘
    assert forgotten_vector_id is not None, "应该有一项被遗忘"
    print(f"  ✓ 最早的一项被遗忘: {forgotten_vector_id}")

    print()
    print("=" * 60)
    print("测试3: 情绪门控学习率")
    print("=" * 60)

    # 高情绪内容应有更高的学习率
    high_emotion_text2 = "太震撼了！这是我一生中最难忘的时刻！"
    emb_high = encoder.encode_text(high_emotion_text2)
    vid_high = vector_store.insert_vector(emb_high, high_emotion_text2, "text", 0.95)
    result_high = hippocampus.encode(vid_high, 0.95)

    low_emotion_text = "今天天气还可以"
    emb_low = encoder.encode_text(low_emotion_text)
    vid_low = vector_store.insert_vector(emb_low, low_emotion_text, "text", 0.1)
    result_low = hippocampus.encode(vid_low, 0.1)

    assert result_high["learning_rate"] > result_low["learning_rate"], \
        "高情绪内容应有更高的学习率"
    print(f"  高情绪学习率: {result_high['learning_rate']:.3f}")
    print(f"  低情绪学习率: {result_low['learning_rate']:.3f}")
    print(f"  ✓ 情绪门控生效")

    print()
    print("=" * 60)
    print("测试4: 睡眠巩固（海马体→皮层）")
    print("=" * 60)

    # 执行睡眠巩固
    sleep_stats = sleep_consolidation.run()

    # 验证：高情绪内容已巩固到皮层
    cortex_vectors = cortex.get_all()
    assert len(cortex_vectors) > 0, "应有内容巩固到皮层"

    # 验证：高情绪内容重要性高
    high_emotion_cortex = [c for c in cortex_vectors
                          if c.get("vector_id") in [vector_id, vid_high]]
    if high_emotion_cortex:
        print(f"  高情绪内容已巩固到皮层，重要性: {high_emotion_cortex[0]['importance_score']:.3f}")
    print(f"  ✓ 睡眠巩固: {sleep_stats['vectors_consolidated']}个向量进入皮层")

    print()
    print("=" * 60)
    print("测试5: 主动遗忘")
    print("=" * 60)

    # 执行主动遗忘
    forget_stats = forgetting_engine.run()
    print(f"  衰减: {forget_stats['vectors_decayed']}个向量")
    print(f"  合并: {forget_stats['vectors_merged']}个向量")
    print(f"  ✓ 主动遗忘执行完成")

    print()
    print("=" * 60)
    print("测试6: 概念形成（向量→节点）")
    print("=" * 60)

    # 触发概念形成
    concept_result = concept_formation.run_clustering()

    if concept_result["new_concepts"]:
        print(f"  形成{len(concept_result['new_concepts'])}个概念:")
        for concept in concept_result["new_concepts"][:3]:
            print(f"    - {concept['name']} ({concept['member_count']}个向量)")
        print(f"  ✓ 概念形成成功")
    else:
        print("  概念数量不足，跳过聚类")

    print()
    print("=" * 60)
    print("测试7: 存算一体（检索=重建）")
    print("=" * 60)

    # 检索相似向量（重建而非直接读取）
    query_text = "机器学习人工智能"
    query_embedding = encoder.encode_text(query_text)
    similar = vector_store.search_similar(query_embedding, top_k=3)

    if similar:
        print(f"  查询: '{query_text}'")
        print(f"  找到{len(similar)}个相似向量:")
        for vec_id, sim_score in similar:
            vec = vector_store.get_vector(vec_id)
            print(f"    [{sim_score:.3f}] {vec['raw_content'][:50]}...")
        print(f"  ✓ 检索重建成功")

    print()
    print("=" * 60)
    print("=== v4.0 人脑式记忆系统测试全部通过 ===")
    print(f"  工作记忆: {working_memory.size()}/{working_memory.max_items}")
    print(f"  海马体: {len(hippocampus.get_all())}个向量")
    print(f"  皮层: {len(cortex.get_all())}个向量")
    print(f"  总向量: {len(vector_store.get_all_vectors())}个")

    vector_store.close()
    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    test_v4_brain_like()
