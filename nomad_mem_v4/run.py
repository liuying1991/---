"""
NomadMem v5.0 — Jarvis AI管家系统
基于人脑式记忆架构的智能对话助手

使用方式:
  python run.py            # 默认: 音频监控模式（v4兼容）
  python run.py chat       # CLI交互对话模式
  python run.py serve      # 启动Web服务
"""
import os
import sys
import time
import json
import yaml
import logging
import psutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

# v5 新模块
from nomad_mem.llm.engine import LLMEngine
from nomad_mem.dialog.manager import DialogManager
from nomad_mem.memory_bridge import MemoryBridge
from nomad_mem.skills.registry import SkillRegistry
from nomad_mem.skills.files import Sandbox, ReadFile, WriteFile, ListFiles

# 自主意识、持久化、审计
from nomad_mem.autonomy.driver import AutonomyDriver
from nomad_mem.persistence.history import ConversationHistory
from nomad_mem.audit_logger import AuditLogger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis")


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

    work_dir = config.get("skills", {}).get("work_dir", "")
    if work_dir:
        os.makedirs(work_dir, exist_ok=True)


def init_memory_system(config):
    """初始化记忆系统"""
    encoder = MultimodalEncoder(config)
    vector_store = VectorStore(config["database"]["vectors_path"])
    hippocampus = Hippocampus(vector_store.conn, config)
    cortex = Cortex(vector_store.conn, config)
    working_memory = WorkingMemory(max_items=config["attention"]["working_memory_limit"])
    attention_scorer = AttentionScorerV4(config)
    concept_formation = ConceptFormation(vector_store.conn, config)
    sleep_consolidation = SleepConsolidation(vector_store.conn, config)
    forgetting_engine = ForgettingEngine(vector_store.conn, config)

    return {
        "encoder": encoder,
        "vector_store": vector_store,
        "hippocampus": hippocampus,
        "cortex": cortex,
        "working_memory": working_memory,
        "attention_scorer": attention_scorer,
        "concept_formation": concept_formation,
        "sleep_consolidation": sleep_consolidation,
        "forgetting_engine": forgetting_engine,
    }


def init_v5_agent(config, memory_system):
    """初始化v5智能体（LLM + 对话 + 技能 + 记忆桥接）"""
    # 1. LLM引擎
    llm_config = config.get("llm", {})
    llm_engine = LLMEngine(llm_config)

    # 2. 记忆桥接
    memory_bridge = MemoryBridge(
        vector_store=memory_system["vector_store"],
        encoder=memory_system["encoder"],
        working_memory=memory_system["working_memory"],
        hippocampus=memory_system["hippocampus"],
        cortex=memory_system["cortex"],
        attention_scorer=memory_system["attention_scorer"],
    )

    # 3. 技能注册
    skill_registry = SkillRegistry()
    skills_config = config.get("skills", {})
    work_dir = skills_config.get("work_dir", "/tmp")
    sandbox = Sandbox(work_dir)

    # 注册文件技能
    skill_registry.register(ReadFile(sandbox))
    skill_registry.register(WriteFile(sandbox))
    skill_registry.register(ListFiles(sandbox))

    # 注册记忆技能
    from nomad_mem.skills.memory import MemoryRecall, MemoryStore, MemoryStatus
    skill_registry.register(MemoryRecall(memory_bridge))
    skill_registry.register(MemoryStore(memory_bridge))
    skill_registry.register(MemoryStatus(memory_bridge))

    # 注册系统技能
    try:
        from nomad_mem.skills.system import SystemInfo, Process, DiskUsage, MemoryUsage
        skill_registry.register(SystemInfo())
        skill_registry.register(Process())
        skill_registry.register(DiskUsage())
        skill_registry.register(MemoryUsage())
    except ImportError:
        logger.warning("psutil未安装，系统技能不可用")

    # 注册命令技能
    from nomad_mem.skills.command import ExecuteCommand
    skill_registry.register(ExecuteCommand(skills_config))

    # 注册工具技能
    from nomad_mem.skills.tools import Calculate, GetDatetime, WebSearch, HttpRequest
    skill_registry.register(Calculate())
    skill_registry.register(GetDatetime())
    skill_registry.register(WebSearch())
    skill_registry.register(HttpRequest())

    # 4. 对话管理器
    dialog_config = config.get("dialog", {})
    dialog_manager = DialogManager(
        llm_engine=llm_engine,
        memory_bridge=memory_bridge,
        skill_registry=skill_registry,
        config=dialog_config,
    )

    # 5. 自主意识驱动
    autonomy_config = config.get("autonomy", {})
    autonomy_driver = AutonomyDriver(dialog_manager=dialog_manager, config=autonomy_config)

    # 6. 持久化
    db_path = config["database"].get("path", "data/nomad_mem.db")
    history_dir = os.path.join(os.path.dirname(db_path), "history")
    history_db = os.path.join(history_dir, "conversation_history.db")
    conversation_history = ConversationHistory(history_db)

    # 7. 审计日志
    audit_log_dir = config.get("audit", {}).get("log_dir", "data/audit")
    audit_logger = AuditLogger(log_dir=audit_log_dir)

    return {
        "llm_engine": llm_engine,
        "memory_bridge": memory_bridge,
        "skill_registry": skill_registry,
        "dialog_manager": dialog_manager,
        "autonomy_driver": autonomy_driver,
        "conversation_history": conversation_history,
        "audit_logger": audit_logger,
    }


def _build_autonomy_context(memory_system, memory_bridge):
    """构建自主意识感知的上下文"""
    mem_summary = memory_bridge.get_memory_summary()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "disk_usage": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
        "memory_usage": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent,
        },
        "working_memory": {
            "size": memory_system["working_memory"].size(),
            "max": memory_system["working_memory"].max_items,
        },
        "total_vectors": mem_summary["total_vectors"],
        "current_hour": time.localtime().tm_hour,
        "last_consolidation_time": time.time(),  # 简化处理
        "consolidation_interval": 21600,
    }


def run_chat_mode(config, memory_system, v5_agent):
    """CLI交互对话模式"""
    dialog_manager = v5_agent["dialog_manager"]
    memory_bridge = v5_agent["memory_bridge"]
    autonomy_driver = v5_agent["autonomy_driver"]
    conversation_history = v5_agent["conversation_history"]
    audit_logger = v5_agent["audit_logger"]
    skill_names = v5_agent["skill_registry"].get_skill_names()

    # 加载持久化的历史
    history = conversation_history.load_history()
    if history:
        dialog_manager.history = history
        print(f"[已加载 {len(history)} 条历史消息]")

    # 记录启动事件
    audit_logger.log_system_event("startup", f"CLI模式启动，已加载{len(history)}条历史")
    audit_logger.log_system_event("skills", f"已注册技能: {', '.join(skill_names)}")

    print("=" * 50)
    print("  Jarvis v5.0 - CLI对话模式")
    print(f"  技能: {len(skill_names)}个")
    print(f"  记忆: {memory_bridge.get_memory_summary()['total_vectors']}条")
    print(f"  历史: {len(history)}条")
    print("=" * 50)
    print("输入 'quit'/'exit' 退出，'clear' 清空历史，'status' 查看状态，'autonomy' 触发自主扫描")
    print()

    try:
        while True:
            user_input = input("你: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("再见！")
                break
            elif user_input.lower() == "clear":
                dialog_manager.clear_history()
                conversation_history.clear_history()
                print("[已清空对话历史]")
                continue
            elif user_input.lower() == "status":
                summary = memory_bridge.get_memory_summary()
                hist_stats = conversation_history.get_stats()
                auton_status = autonomy_driver.get_status()
                print(f"\n=== 记忆系统 ===")
                print(f"总记忆: {summary['total_vectors']}")
                print(f"工作记忆: {summary['working_memory']}")
                if summary.get("by_type"):
                    print("类型分布:")
                    for t, c in summary["by_type"].items():
                        print(f"  {t}: {c}")
                print(f"\n=== 持久化 ===")
                print(f"保存消息: {hist_stats['message_count']}")
                print(f"技能调用: {hist_stats['skill_call_count']}")
                print(f"\n=== 自主意识 ===")
                print(f"传感器: {', '.join(auton_status['sensors'])}")
                print(f"行动历史: {auton_status['action_history_count']}条")
                continue
            elif user_input.lower() == "autonomy":
                context = _build_autonomy_context(memory_system, memory_bridge)
                results = autonomy_driver.cycle(context)
                if results:
                    print("\n[自主行动]:")
                    for r in results:
                        print(f"  {r}")
                else:
                    print("[自主扫描] 暂无需要执行的行动")
                continue

            # 记录用户消息
            audit_logger.log_user_message(user_input)
            autonomy_driver.on_user_interaction()

            response = dialog_manager.chat(user_input)

            # 持久化保存
            conversation_history.save_message("user", user_input)
            conversation_history.save_message("assistant", response)
            audit_logger.log_user_message(user_input, response=response)

            print(f"\nJarvis: {response}\n")

    except KeyboardInterrupt:
        print("\n再见！")
    except Exception as e:
        audit_logger.log_system_event("error", str(e), level="error")
        raise
    finally:
        v5_agent["llm_engine"].close()
        memory_system["vector_store"].close()
        conversation_history.close()
        audit_logger.close()


def run_serve_mode(config, memory_system, v5_agent):
    """Web服务模式"""
    from nomad_mem.web.server import create_app
    import uvicorn

    web_config = config.get("web", {})
    host = web_config.get("host", "0.0.0.0")
    port = web_config.get("port", 8080)
    debug = web_config.get("debug", False)

    v5_agent["audit_logger"].log_system_event("startup", f"Web服务模式启动 http://{host}:{port}")

    app = create_app(v5_agent["dialog_manager"], web_config)

    print("=" * 50)
    print("  Jarvis v5.0 - Web服务模式")
    print(f"  地址: http://{host}:{port}")
    print(f"  技能: {len(v5_agent['skill_registry'].get_skill_names())}个")
    print(f"  记忆: {v5_agent['memory_bridge'].get_memory_summary()['total_vectors']}条")
    print("=" * 50)
    print("按 Ctrl+C 停止服务")
    print()

    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        v5_agent["llm_engine"].close()
        memory_system["vector_store"].close()
        v5_agent["conversation_history"].close()
        v5_agent["audit_logger"].close()


def run_audio_mode(config, memory_system):
    """音频监控模式（v4兼容）"""
    encoder = memory_system["encoder"]
    vector_store = memory_system["vector_store"]
    hippocampus = memory_system["hippocampus"]
    cortex = memory_system["cortex"]
    working_memory = memory_system["working_memory"]
    attention_scorer = memory_system["attention_scorer"]
    concept_formation = memory_system["concept_formation"]
    sleep_consolidation = memory_system["sleep_consolidation"]
    forgetting_engine = memory_system["forgetting_engine"]

    input_dir = config["audio"]["input_dir"]
    processed_dir = config["audio"]["processed_dir"]
    formats = config["audio"]["supported_formats"]

    print("[NomadMem v5.0] 音频监控模式（v4兼容）")
    print(f"[v5.0] 工作记忆限制: {working_memory.max_items}项")
    print(f"[v5.0] 监控音频目录: {input_dir}")
    print("[v5.0] 输入 'shell' 进入交互模式，Ctrl+C 停止")

    last_sleep_time = 0
    last_forget_time = 0

    try:
        while True:
            # 处理音频
            if os.path.exists(input_dir):
                files = [f for f in os.listdir(input_dir)
                         if any(f.lower().endswith(ext) for ext in formats)]

                for fname in files:
                    audio_path = os.path.join(input_dir, fname)
                    print(f"[AUDIO v5.0] 处理: {fname}")

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
                    for cv in cortex_vectors[:10]:
                        cortex_emb = vector_store.get_embedding(cv["vector_id"])
                        if cortex_emb is not None:
                            cortex_embeddings.append(cortex_emb)

                    attention = attention_scorer.score(
                        embedding, emotion_score, wm_embeddings, cortex_embeddings
                    )
                    print(f"  注意力分数: {attention:.3f}")

                    # 5. 更新工作记忆
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
        print("\n[NomadMem v5.0] 已停止")
        vector_store.close()


def main():
    """主入口"""
    # 解析命令行参数
    mode = "audio"  # 默认模式
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    config = load_config()
    ensure_dirs(config)

    # 初始化记忆系统（所有模式都需要）
    memory_system = init_memory_system(config)

    # 根据模式启动
    if mode == "chat":
        v5_agent = init_v5_agent(config, memory_system)
        run_chat_mode(config, memory_system, v5_agent)
    elif mode == "serve":
        v5_agent = init_v5_agent(config, memory_system)
        run_serve_mode(config, memory_system, v5_agent)
    elif mode == "audio":
        run_audio_mode(config, memory_system)
    else:
        print(f"未知模式: {mode}")
        print("可用模式: audio(默认), chat, serve")
        sys.exit(1)


if __name__ == "__main__":
    main()
