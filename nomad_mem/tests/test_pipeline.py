"""
端到端测试：验证万物皆节点 + 万物关联 + 自由标签
"""
import os
import sys
import tempfile
import shutil
import json
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nomad_mem.memory.store import MemoryStore
from nomad_mem.memory.graph import MemoryGraph
from nomad_mem.attention.scorer import AttentionScorer
from nomad_mem.discovery.patterns import PatternDiscovery
from nomad_mem.personality.extractor import PersonalityExtractor


def load_config():
    """加载测试配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    tmpdir = tempfile.mkdtemp()
    cfg["database"]["path"] = os.path.join(tmpdir, "test_memory.db")
    cfg["audio"]["input_dir"] = os.path.join(tmpdir, "audio_in")
    cfg["audio"]["processed_dir"] = os.path.join(tmpdir, "audio_processed")
    os.makedirs(cfg["audio"]["input_dir"], exist_ok=True)
    os.makedirs(cfg["audio"]["processed_dir"], exist_ok=True)

    return cfg, tmpdir


def test_universal_nodes_and_edges():
    """
    核心测试：万物皆节点，万物皆关联。
    混合物理实体、感官片段、抽象概念、虚构产物和情感——
    全部作为平等节点参与关联。
    """
    cfg, tmpdir = load_config()
    store = MemoryStore(db_path=cfg["database"]["path"])

    # ===== 创建各类节点 =====

    # 可感知对象
    zhangsan = store.upsert_node("张三", "一位30岁的男性", "person")
    suit = store.upsert_node("黑色西装", "一套定制的黑色西装", "object")
    shoes = store.upsert_node("黑色皮鞋", "亮面牛津鞋", "object")

    # 感官片段
    audio = store.upsert_node("raw:录音_20260609_001", "张三走进会议室，穿着黑色西装...", "sensory_audio")

    # 空间
    room = store.upsert_node("会议室A", "中型会议室，位于8楼", "spatial")

    # 抽象概念
    first_principle = store.upsert_node("第一性原理", "从最基本的真理出发重新思考问题", "abstract")

    # 虚构/假设
    dream = store.upsert_node("昨晚的梦", "梦到一个没有颜色的世界", "fictional")

    # 情感
    fear = store.upsert_node("恐惧", "一种强烈的负面情绪", "emotion")

    # ===== 建立万物关联 =====

    # 感官片段 → 人物
    store.upsert_edge(audio, zhangsan, "提到")

    # 感官片段 → 空间
    store.upsert_edge(audio, room, "发生在")

    # 人物 → 衣着
    store.upsert_edge(zhangsan, suit, "穿着")

    # 人物 → 空间
    store.upsert_edge(zhangsan, room, "位于")

    # 物体间关联
    store.upsert_edge(suit, shoes, "颜色匹配")

    # 抽象概念 → 方法论（抽象概念之间）
    store.upsert_edge(first_principle, room, "应用于场景")

    # 虚构 → 情感
    store.upsert_edge(dream, fear, "引发情绪")

    # 情感 → 生理
    heartbeat = store.upsert_node("心跳加速", "心率超过100bpm", "physiology")
    store.upsert_edge(fear, heartbeat, "关联生理")

    # 跨类型大跨度关联：梦 → 抽象概念
    store.upsert_edge(dream, first_principle, "隐喻关联")

    # ===== 验证节点 =====
    all_nodes = store.get_all_nodes()
    assert len(all_nodes) == 9, f"期望9个节点，实际{len(all_nodes)}"

    # ===== 验证关联 =====
    all_edges = store.get_all_edges()
    assert len(all_edges) == 9, f"期望9条边，实际{len(all_edges)}"

    # ===== 验证跨类型关联成立 =====

    # 张三的邻居应该包含黑色西装和会议室
    conn = store.get_connected_nodes(zhangsan)
    conn_names = [n["name"] for n in conn]
    assert "黑色西装" in conn_names, f"张三应关联黑色西装，实际: {conn_names}"
    assert "会议室A" in conn_names, f"张三应关联会议室A，实际: {conn_names}"

    # 昨晚的梦的邻居应包含恐惧和第一性原理
    conn_dream = store.get_connected_nodes(dream)
    conn_dream_names = [n["name"] for n in conn_dream]
    assert "恐惧" in conn_dream_names
    assert "第一性原理" in conn_dream_names

    # ===== 验证自由标签 =====
    store.set_tag(zhangsan, "性别", "男")
    store.set_tag(zhangsan, "身高", "175cm")
    store.set_tag(zhangsan, "体型", "偏瘦")
    store.set_tag(zhangsan, "脸型", "瓜子脸")
    store.set_tag(zhangsan, "五官", "浓眉大眼")
    store.set_tag(zhangsan, "表情", "微笑中带严肃")
    store.set_tag(zhangsan, "手指", "修长、指甲干净")
    store.set_tag(zhangsan, "衣服颜色", "黑色")
    store.set_tag(zhangsan, "包", "无")
    store.set_tag(zhangsan, "头发", "短发、直发、黑色")
    store.set_tag(zhangsan, "眼镜", "无")
    store.set_tag(zhangsan, "语气", "沉稳")
    store.set_tag(zhangsan, "职业推测", "商务人士")
    store.set_tag(zhangsan, "年龄段", "30-35岁")

    all_tags = store.get_all_tags(zhangsan)
    assert len(all_tags) == 14
    assert all_tags["性别"] == "男"
    assert all_tags["职业推测"] == "商务人士"

    # ===== 验证 get_nodes_by_tag =====
    results = store.get_nodes_by_tag("性别", "男")
    assert len(results) >= 1
    assert results[0]["name"] == "张三"

    # ===== 验证图构建 =====
    graph = MemoryGraph(store)
    graph.rebuild()
    g = graph.get_graph()
    assert len(g.nodes) == 9
    assert len(g.edges) == 9  # NetworkX无向图，9条无向边

    # 验证跨类型路径
    path = graph.find_path("昨晚的梦", "心跳加速")
    assert path is not None, "梦到恐惧到心跳加速应有路径"
    print(f"  跨类型路径: {' → '.join(path)}")

    print("=== 万物皆节点测试全部通过 ===")
    print(f"  节点数: {len(all_nodes)}")
    print(f"  边数: {len(all_edges)}")
    print(f"  张三标签: {json.dumps(all_tags, ensure_ascii=False, indent=2)}")

    shutil.rmtree(tmpdir)


def test_full_pipeline():
    """全流程测试"""
    cfg, tmpdir = load_config()
    store = MemoryStore(db_path=cfg["database"]["path"])
    graph = MemoryGraph(store)
    scorer = AttentionScorer(cfg, store)
    discovery = PatternDiscovery(store, graph, cfg)
    extractor = PersonalityExtractor(store, graph)

    test_text = "人工智能需要从经验中学习模式识别和决策能力"
    audio_nid = store.upsert_node("raw:test_audio", test_text, "sensory_audio")

    try:
        import jieba
        concepts = list(set([w for w in jieba.lcut(test_text) if len(w) >= 2]))
    except ImportError:
        concepts = ["人工智能", "经验", "学习", "模式识别", "决策能力"]

    concept_ids = []
    for cname in concepts:
        cid = store.upsert_node(cname, test_text, "concept")
        concept_ids.append(cid)
        store.upsert_edge(audio_nid, cid, "提到")

    for i in range(len(concept_ids)):
        for j in range(i + 1, len(concept_ids)):
            store.upsert_edge(concept_ids[i], concept_ids[j], "co-occurrence")

    graph.rebuild()
    score = scorer.score(test_text, graph.get_graph(), 0.5)
    assert 0.0 <= score <= 1.0

    results = discovery.run()
    assert "hub_nodes" in results
    assert "clusters" in results
    assert "communities" in results

    personality = extractor.extract()
    assert "thinking_patterns" in personality
    assert "values" in personality
    assert "decision_style" in personality
    assert "language_style" in personality

    print("=== 全流程测试通过 ===")
    print(f"  注意力分数: {score:.3f}")
    print(f"  枢纽节点: {results['hub_nodes']}")

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    print("=" * 60)
    print("测试1: 万物皆节点 — 跨类型关联")
    print("=" * 60)
    test_universal_nodes_and_edges()

    print()
    print("=" * 60)
    print("测试2: 全流程管线")
    print("=" * 60)
    test_full_pipeline()
