"""
NomadMem v4.0 — 人脑式自主AI记忆系统主入口
"""
import os
import sys
import time
import json
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from nomad_mem.encoder.multimodal import MultimodalEncoder
from nomad_mem.encoder.emotion_detector import EmotionDetector
from nomad_mem.memory.vector_store import VectorStore
from nomad_mem.memory.hippocampus import Hippocampus
from nomad_mem.memory.cortex import Cortex
from nomad_mem.memory.working_memory import WorkingMemory
from nomad_mem.memory.forget import ForgettingEngine
from nomad_mem.graph.concept_formation import ConceptFormation
from nomad_mem.graph.graph_builder import GraphBuilder
from nomad_mem.sleep.consolidation import SleepConsolidation
from nomad_mem.attention.scorer_v4 import AttentionScorerV4


def load_config(path="config.yaml"):
    """加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(config):
    """确保目录存在"""
    for d in [config["audio"]["input_dir"], config["audio"]["processed_dir"]]:
        os.makedirs(d, exist_ok=True)

    db_dir = os.path.dirname(config["database"]["path"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    vectors_dir = os.path.dirname(config["database"]["vectors_path"])
    if vectors_dir:
        os.makedirs(vectors_dir, exist_ok=True)


def process_audio_v4(config, encoder, vector_store, hippocampus, cortex,
                     working_memory, attention_scorer, concept_formation):
    """处理音频文件（v4.0版本）"""
    input_dir = config["audio"]["input_dir"]
    processed_dir = config["audio"]["processed_dir"]
    formats = config["audio"]["supported_formats"]

    if not os.path.exists(input_dir):
        return

    files = [f for f in os.listdir(input_dir)
             if any(f.lower().endswith(ext) for ext in formats)]

    for fname in files:
        audio_path = os.path.join(input_dir, fname)
        print(f"[AUDIO v4.0] 处理: {fname}")

        # 1. 多模态编码 → 向量
        embedding, text, emotion_score = encoder.encode_audio(audio_path)

        # 2. 计算新颖性
        similar = vector_store.search_similar(embedding, top_k=10)
        if similar:
            novelty_score = 1.0 - np.mean([sim for _, sim in similar])
        else:
            novelty_score = 1.0

        # 3. 海马体快写
        vector_id = vector_store.insert_vector(
            embedding, text, "audio", emotion_score
        )
        vector_store.update_novelty(vector_id, novelty_score)

        # 情绪门控编码
        hippocampus.encode(vector_id, emotion_score)
        print(f"  海马体编码: vector_id={vector_id}, emotion={emotion_score:.2f}")

        # 4. 计算注意力分数
        wm_embeddings = []
        for wm_id in working_memory.get_current_focus():
            wm_emb = vector_store.get_embedding(wm_id)
            if wm_emb is not None:
                wm_embeddings.append(wm_emb)

        cortex_embeddings = []
        cortex_vectors = cortex.get_all()
        for cv in cortex_vectors[:10]:  # 只取前10个皮层向量
            cortex_emb = vector_store.get_embedding(cv["vector_id"])
            if cortex_emb is not None:
                cortex_embeddings.append(cortex_emb)

        attention = attention_scorer.score(
            embedding, emotion_score, wm_embeddings, cortex_embeddings
        )
        print(f"  注意力分数: {attention:.3f}")

        # 5. 更新工作记忆（硬性4项限制）
        forgotten = working_memory.add(vector_id, attention)
        if forgotten:
            print(f"  工作记忆遗忘: vector_id={forgotten[0]}")

        # 6. 更新最后访问时间
        vector_store.update_last_accessed(vector_id)

        # 7. 概念形成检查
        all_vectors = vector_store.get_all_vectors()
        if len(all_vectors) % config["discovery"]["clustering_interval"] == 0:
            print("[CONCEPT] 触发概念形成...")
            concept_formation.run_clustering()

        # 8. 移动已处理文件
        dest = os.path.join(processed_dir, fname)
        os.rename(audio_path, dest)
        print(f"  -> 已移动到 {dest}")


def main():
    """主入口"""
    config = load_config()
    ensure_dirs(config)

    # 初始化各模块
    encoder = MultimodalEncoder(config)
    vector_store = VectorStore(config["database"]["vectors_path"])
    hippocampus = Hippocampus(vector_store.conn, config)
    cortex = Cortex(vector_store.conn, config)
    working_memory = WorkingMemory(max_items=config["attention"]["working_memory_limit"])
    attention_scorer = AttentionScorerV4(config)
    concept_formation = ConceptFormation(vector_store.conn, config)
    sleep_consolidation = SleepConsolidation(vector_store.conn, config)
    forgetting_engine = ForgettingEngine(vector_store.conn, config)

    print("[NomadMem v4.0] 人脑式自主AI记忆系统")
    print(f"[v4.0] 工作记忆限制: {working_memory.max_items}项")
    print(f"[v4.0] 监控音频目录: {config['audio']['input_dir']}")
    print("[v4.0] 输入 'shell' 进入交互模式，Ctrl+C 停止")

    last_sleep_time = 0
    last_forget_time = 0

    try:
        while True:
            # 处理音频
            process_audio_v4(config, encoder, vector_store, hippocampus, cortex,
                           working_memory, attention_scorer, concept_formation)

            now = time.time()

            # 睡眠巩固（每6小时）
            if now - last_sleep_time > config["sleep"]["consolidation_interval"]:
                print("[SLEEP] 开始睡眠巩固...")
                sleep_stats = sleep_consolidation.run()
                print(f"  巩固: {sleep_stats['vectors_consolidated']}个向量")
                print(f"  提升: {sleep_stats['vectors_promoted']}个向量")
                print(f"  移除: {sleep_stats['vectors_removed']}个向量")
                last_sleep_time = now

            # 主动遗忘（每小时）
            if now - last_forget_time > 3600:
                print("[FORGET] 执行主动遗忘...")
                forget_stats = forgetting_engine.run()
                print(f"  衰减: {forget_stats['vectors_decayed']}个向量")
                print(f"  合并: {forget_stats['vectors_merged']}个向量")
                print(f"  修剪: {forget_stats['edges_pruned']}条边")
                last_forget_time = now

            # 显示状态
            print(f"\n[状态] 工作记忆: {working_memory.size()}/{working_memory.max_items}")
            print(f"[状态] 海马体: {len(hippocampus.get_all())}个向量")
            print(f"[状态] 皮层: {len(cortex.get_all())}个向量")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[NomadMem v4.0] 已停止")
        vector_store.close()


if __name__ == "__main__":
    main()
