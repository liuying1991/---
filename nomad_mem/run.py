"""
NomadMem — 自主AI记忆系统主入口（v3.0 万物皆节点）
"""
import os
import sys
import time
import json
import yaml

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nomad_mem.audio.transcriber import AudioTranscriber
from nomad_mem.memory.store import MemoryStore
from nomad_mem.memory.graph import MemoryGraph
from nomad_mem.attention.scorer import AttentionScorer
from nomad_mem.discovery.patterns import PatternDiscovery
from nomad_mem.personality.extractor import PersonalityExtractor


def load_config(path="config.yaml"):
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(config):
    """确保目录存在"""
    for d in [config["audio"]["input_dir"], config["audio"]["processed_dir"]]:
        os.makedirs(d, exist_ok=True)

    # 数据库目录
    db_dir = os.path.dirname(config["database"]["path"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def process_audio_files(config, transcriber, store, graph, scorer):
    """处理音频文件"""
    input_dir = config["audio"]["input_dir"]
    processed_dir = config["audio"]["processed_dir"]
    formats = config["audio"]["supported_formats"]

    if not os.path.exists(input_dir):
        return

    files = [f for f in os.listdir(input_dir)
             if any(f.lower().endswith(ext) for ext in formats)]

    for fname in files:
        audio_path = os.path.join(input_dir, fname)
        print(f"[AUDIO] 处理: {fname}")

        result = transcriber.transcribe(audio_path)
        transcript = result["text"]
        duration = result["duration"]
        emotion_score = result["emotion_score"]

        # 1. 音频片段作为节点存入
        audio_node_name = f"raw:录音_{os.path.splitext(fname)[0]}"
        audio_node_id = store.upsert_node(
            name=audio_node_name,
            content=transcript,
            node_type="sensory_audio"
        )

        # 给音频节点打标签
        store.set_tag(audio_node_id, "时长", str(duration))
        store.set_tag(audio_node_id, "情感评分", f"{emotion_score:.2f}")
        store.set_tag(audio_node_id, "来源文件", audio_path)

        # 2. 注意力评分
        graph.rebuild()
        attn_score = scorer.score(transcript, graph.get_graph(), emotion_score)
        print(f"  attention_score={attn_score:.3f}")

        # 3. 从文本中提取概念节点，建立关联
        concept_names = _extract_concepts(transcript)
        for cname in concept_names:
            cid = store.upsert_node(cname, transcript, "concept")

            # 音频片段 → 概念（"提到"关系）
            store.upsert_edge(audio_node_id, cid, "提到")

            # 自动推测标签
            auto_tags = _infer_tags(transcript, cname)
            for tag_key, tag_val in auto_tags.items():
                store.set_tag(cid, tag_key, tag_val)

        # 概念间共现关联
        concept_ids = []
        for cname in concept_names:
            node = store.get_node_by_name(cname)
            if node:
                concept_ids.append(node["id"])

        for i, cid_a in enumerate(concept_ids):
            for cid_b in concept_ids[i+1:]:
                store.upsert_edge(cid_a, cid_b, "co-occurrence")

        # 4. 移动已处理文件
        dest = os.path.join(processed_dir, fname)
        os.rename(audio_path, dest)
        print(f"  -> 已移动到 {dest}")


def _extract_concepts(text: str) -> list:
    """使用jieba分词，取长度>=2的词语作为概念"""
    try:
        import jieba
    except ImportError:
        return [w for w in text.replace("，", " ").replace("。", " ").split() if len(w) >= 2]

    words = jieba.lcut(text)
    return list(set([w for w in words if len(w) >= 2]))


def _infer_tags(text: str, concept_name: str) -> dict:
    """从文本中自动推测节点标签"""
    tags = {}

    if "男" in text and "女" not in text:
        tags["性别"] = "男"
    elif "女" in text:
        tags["性别"] = "女"

    if "长发" in text:
        tags["头发"] = "长发"
    elif "短发" in text:
        tags["头发"] = "短发"

    colors = ["红", "橙", "黄", "绿", "蓝", "紫", "黑", "白", "灰", "棕", "粉"]
    for c in colors:
        if c in text:
            tags["涉及颜色"] = c
            break

    if "笑" in text or "开心" in text:
        tags["表情"] = "开心"
    elif "怒" in text or "生气" in text:
        tags["表情"] = "生气"

    return tags


def interactive_mode(store, graph):
    """交互式模式：手动管理节点、标签和关联"""
    print("\n=== 交互模式 ===")
    print("命令:")
    print("  node <名称> [类型]      创建/查看节点")
    print("  tag <节点名> <标签> <值>  为节点添加标签")
    print("  link <节点A> <节点B> <关系>  建立关联")
    print("  path <节点A> <节点B>    查找最短路径")
    print("  search <关键词>         搜索节点")
    print("  tags <节点名>           查看节点所有标签")
    print("  edges <节点名>          查看节点所有关联")
    print("  quit                    退出")

    while True:
        try:
            cmd = input("nomad> ").strip()
        except EOFError:
            break

        if cmd == "quit":
            break

        parts = cmd.split(" ", 2)
        if not parts:
            continue

        action = parts[0]

        if action == "node" and len(parts) >= 2:
            name = parts[1]
            ntype = parts[2] if len(parts) > 2 else "general"
            nid = store.upsert_node(name, "", ntype)
            node = store.get_node(nid)
            print(f"  节点: [{nid}] {node['name']} ({node['node_type']})")

        elif action == "tag" and len(parts) >= 3:
            node_name = parts[1]
            rest = parts[2].split(" ", 1)
            tag_name = rest[0]
            tag_value = rest[1] if len(rest) > 1 else ""
            node = store.get_node_by_name(node_name)
            if node:
                store.set_tag(node["id"], tag_name, tag_value)
                print(f"  已设置: [{node_name}] {tag_name} = {tag_value}")
            else:
                print(f"  节点不存在: {node_name}")

        elif action == "link" and len(parts) >= 3:
            rest = parts[1] + " " + parts[2]
            args = rest.rsplit(" ", 1)
            if len(args) >= 2:
                names = args[0].rsplit(" ", 1)
                if len(names) >= 2:
                    node_a = store.get_node_by_name(names[0])
                    node_b = store.get_node_by_name(names[1])
                    edge_type = args[1]
                    if node_a and node_b:
                        store.upsert_edge(node_a["id"], node_b["id"], edge_type)
                        print(f"  已关联: [{names[0]}] --{edge_type}--> [{names[1]}]")
                    else:
                        print("  节点不存在")

        elif action == "path" and len(parts) >= 2:
            names = parts[1].rsplit(" ", 1)
            if len(names) >= 2:
                graph.rebuild()
                path = graph.find_path(names[0], names[1])
                if path:
                    print(f"  路径: {' → '.join(path)}")
                else:
                    print("  无路径")

        elif action == "search" and len(parts) >= 2:
            keyword = parts[1]
            results = store.search_nodes(keyword)
            for r in results[:20]:
                print(f"  [{r['id']}] {r['name']} ({r['node_type']})")

        elif action == "tags" and len(parts) >= 2:
            node_name = parts[1]
            node = store.get_node_by_name(node_name)
            if node:
                tags = store.get_all_tags(node["id"])
                print(f"  标签: {json.dumps(tags, ensure_ascii=False, indent=2)}")

        elif action == "edges" and len(parts) >= 2:
            node_name = parts[1]
            node = store.get_node_by_name(node_name)
            if node:
                edges = store.get_edges(node_id=node["id"])
                for e in edges:
                    src = store.get_node(e["source_node_id"])
                    tgt = store.get_node(e["target_node_id"])
                    src_name = src["name"] if src else f"#{e['source_node_id']}"
                    tgt_name = tgt["name"] if tgt else f"#{e['target_node_id']}"
                    print(f"  [{src_name}] --{e['edge_type']}--> [{tgt_name}] (str={e['strength']:.1f})")


def main():
    """主入口"""
    config = load_config()
    ensure_dirs(config)

    store = MemoryStore(db_path=config["database"]["path"])
    graph = MemoryGraph(store)
    transcriber = AudioTranscriber(config)
    scorer = AttentionScorer(config, store)
    discovery = PatternDiscovery(store, graph, config)
    extractor = PersonalityExtractor(store, graph)

    print("[NomadMem v3.0] 万物皆节点，万物皆关联")
    print(f"[NomadMem v3.0] 监控音频目录: {config['audio']['input_dir']}")
    print("[NomadMem v3.0] 输入 'shell' 进入交互模式，Ctrl+C 停止")

    last_discovery_time = 0

    try:
        while True:
            # 处理音频文件
            process_audio_files(config, transcriber, store, graph, scorer)

            now = time.time()
            if now - last_discovery_time > config["discovery"]["run_interval_seconds"]:
                graph.rebuild()
                node_count = len(store.get_all_nodes())

                if node_count >= 10:
                    print("[DISCOVERY] 开始模式发现...")
                    patterns = discovery.run()
                    print(f"  枢纽节点: {[c['name'] for c in patterns['hub_nodes']]}")
                    print(f"  社区数: {len(set(patterns['communities'].values()))}")

                    suggestions = patterns.get("new_edge_suggestions", [])
                    for s in suggestions:
                        print(f"  [建议关联] [{s['source']}] --{s['suggested_type']}--> [{s['target']}]")

                    personality = extractor.extract()
                    print(f"  人格特征: {personality['thinking_patterns']}")
                    print(f"  标签统计: {personality.get('tag_statistics', {})}")
                    print(f"  关联类型统计: {personality.get('edge_type_statistics', {})}")

                last_discovery_time = now

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[NomadMem] 已停止")
        store.close()


if __name__ == "__main__":
    main()
