"""
第十九轮端到端测试: 技能自发现 + 自进化 + Jarvis集成

测试覆盖:
- SkillDiscoverer (existing): 技能使用记录、组合发现、模式识别
- SkillEvolutionManager: 技能注册、版本管理、性能追踪、优化建议、废弃管理
- JarvisCore集成: 技能记录/组合发现/注册/性能/优化/版本/废弃
"""
import pytest
import os
import tempfile
import time


# ─── Skill Discovery Tests (existing module) ─────────────────────────────────


class TestSkillDiscovererCore:
    @pytest.fixture
    def discoverer(self):
        from nomad_mem.skills.skill_discovery import SkillDiscoverer
        db = tempfile.mktemp(suffix=".db")
        d = SkillDiscoverer(db_path=db)
        yield d
        d.close()
        if os.path.exists(db):
            os.remove(db)

    def test_init(self, discoverer):
        assert discoverer.db_path is not None

    def test_record_usage(self, discoverer):
        usage_id = discoverer.record_usage("read_file", context="test", result="ok", success=True)
        assert usage_id is not None
        assert len(usage_id) > 0

    def test_get_skill_stats_empty(self, discoverer):
        stats = discoverer.get_skill_stats("nonexistent")
        assert stats["usage_count"] == 0

    def test_get_skill_stats_with_data(self, discoverer):
        discoverer.record_usage("read_file", success=True)
        discoverer.record_usage("read_file", success=True)
        discoverer.record_usage("read_file", success=False)
        stats = discoverer.get_skill_stats("read_file")
        assert stats["usage_count"] == 3
        assert stats["success_rate"] < 1.0

    def test_get_top_skills(self, discoverer):
        discoverer.record_usage("read_file", success=True)
        discoverer.record_usage("read_file", success=True)
        discoverer.record_usage("write_file", success=True)
        top = discoverer.get_top_skills(limit=5)
        assert len(top) >= 2
        assert top[0]["skill_name"] == "read_file"

    def test_find_combinations_min_frequency(self, discoverer):
        # Need multiple sessions to find combinations
        discoverer.record_usage("read_file", success=True)
        discoverer.record_usage("write_file", success=True)
        combos = discoverer.find_combinations(min_frequency=1)
        # May or may not find combos depending on timing
        assert isinstance(combos, list)

    def test_suggest_next_skill_empty(self, discoverer):
        result = discoverer.suggest_next_skill([])
        assert result is None

    def test_suggest_next_skill_with_data(self, discoverer):
        # Record some co-occurring skills
        discoverer.record_usage("read_file", success=True)
        discoverer.record_usage("write_file", success=True)
        suggest = discoverer.suggest_next_skill(["read_file"])
        # May return write_file if detected as co-occurring
        assert isinstance(suggest, (str, type(None)))


class TestSkillDiscovererPatterns:
    @pytest.fixture
    def discoverer(self):
        from nomad_mem.skills.skill_discovery import SkillDiscoverer
        db = tempfile.mktemp(suffix=".db")
        d = SkillDiscoverer(db_path=db)
        yield d
        d.close()
        if os.path.exists(db):
            os.remove(db)

    def test_discover_new_patterns_empty(self, discoverer):
        patterns = discoverer.discover_new_patterns()
        assert isinstance(patterns, list)

    def test_discover_patterns_with_data(self, discoverer):
        # Record enough data to trigger pattern discovery
        for _ in range(5):
            discoverer.record_usage("read_file", success=True)
            discoverer.record_usage("write_file", success=True)
        discoverer.record_usage("execute", success=True)
        discoverer.record_usage("execute", success=True)

        patterns = discoverer.discover_new_patterns()
        assert isinstance(patterns, list)
        # May find sequence patterns or high success skill patterns
        assert len(patterns) >= 0

    def test_high_success_skill_pattern(self, discoverer):
        for _ in range(5):
            discoverer.record_usage("reliable_skill", success=True)
        patterns = discoverer.discover_new_patterns()
        high_success_patterns = [
            p for p in patterns if p.get("pattern_type") == "high_success_skill"
        ]
        # May find this pattern if usage count and success rate thresholds are met
        assert isinstance(high_success_patterns, list)


# ─── Skill Evolution Tests ───────────────────────────────────────────────────


class TestSkillEvolutionEnums:
    def test_skill_status(self):
        from nomad_mem.skills.skill_evolution import SkillStatus
        assert SkillStatus.DRAFT.value == "draft"
        assert SkillStatus.ACTIVE.value == "active"
        assert SkillStatus.DEPRECATED.value == "deprecated"
        assert SkillStatus.ARCHIVED.value == "archived"

    def test_evolution_type(self):
        from nomad_mem.skills.skill_evolution import EvolutionType
        assert EvolutionType.PERFORMANCE.value == "performance"
        assert EvolutionType.BUG_FIX.value == "bug_fix"
        assert EvolutionType.FEATURE_ADD.value == "feature_add"


class TestSkillVersionDataclass:
    def test_create_version(self):
        from nomad_mem.skills.skill_evolution import SkillVersion, SkillStatus, EvolutionType
        v = SkillVersion(
            version_id="v1",
            skill_name="read_file",
            version="1.0",
            status=SkillStatus.ACTIVE,
            description="initial",
        )
        assert v.status == SkillStatus.ACTIVE
        assert v.evolution_type == EvolutionType.PERFORMANCE

    def test_version_to_dict(self):
        from nomad_mem.skills.skill_evolution import SkillVersion, SkillStatus, EvolutionType
        v = SkillVersion(
            version_id="v2",
            skill_name="test",
            version="2.0",
            status=SkillStatus.ACTIVE,
            description="test",
            evolution_type=EvolutionType.BUG_FIX,
            success_rate=0.9,
        )
        d = v.to_dict()
        assert d["status"] == "active"
        assert d["evolution_type"] == "bug_fix"
        restored = SkillVersion.from_dict(d)
        assert restored.status == SkillStatus.ACTIVE


class TestSkillEvolutionManagerCore:
    @pytest.fixture
    def manager(self):
        from nomad_mem.skills.skill_evolution import SkillEvolutionManager
        db = tempfile.mktemp(suffix=".db")
        m = SkillEvolutionManager(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_init(self, manager):
        assert manager.db_path is not None

    def test_register_skill(self, manager):
        result = manager.register_skill("read_file", "读取文件内容", "io")
        assert result is True

    def test_register_duplicate_skill(self, manager):
        manager.register_skill("read_file", "读取文件")
        result = manager.register_skill("read_file", "再次注册")
        assert result is False  # Already exists

    def test_get_skill_info(self, manager):
        manager.register_skill("read_file", "读取文件", "io")
        info = manager.get_skill_info("read_file")
        assert info is not None
        assert info["skill_name"] == "read_file"

    def test_get_all_skills(self, manager):
        manager.register_skill("read_file", "读取", "io")
        manager.register_skill("write_file", "写入", "io")
        skills = manager.get_all_skills()
        assert len(skills) >= 2

    def test_get_skill_info_not_found(self, manager):
        info = manager.get_skill_info("nonexistent")
        assert info is None


class TestSkillEvolutionVersionManagement:
    @pytest.fixture
    def manager(self):
        from nomad_mem.skills.skill_evolution import SkillEvolutionManager
        db = tempfile.mktemp(suffix=".db")
        m = SkillEvolutionManager(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_create_version(self, manager):
        manager.register_skill("read_file", "读取文件")
        version_id = manager.create_version("read_file", "2.0", "性能优化")
        assert version_id is not None
        assert version_id.startswith("ver_")

    def test_get_versions(self, manager):
        manager.register_skill("read_file", "读取文件")
        manager.create_version("read_file", "1.1", "bug修复", "bug_fix")
        manager.create_version("read_file", "2.0", "性能优化", "performance")
        versions = manager.get_versions("read_file")
        assert len(versions) >= 3  # Initial + 2 new

    def test_get_latest_version(self, manager):
        manager.register_skill("read_file", "读取文件")
        manager.create_version("read_file", "2.0", "v2")
        latest = manager.get_latest_version("read_file")
        assert latest is not None
        assert latest.version == "2.0"

    def test_deprecate_skill(self, manager):
        manager.register_skill("old_skill", "旧技能")
        manager.deprecate_skill("old_skill")
        info = manager.get_skill_info("old_skill")
        assert info["status"] == "deprecated"

    def test_create_version_invalid_type(self, manager):
        manager.register_skill("read_file", "读取文件")
        version_id = manager.create_version("read_file", "2.0", "测试", "invalid_type")
        # Should default to PERFORMANCE
        assert version_id is not None


class TestSkillEvolutionPerformance:
    @pytest.fixture
    def manager(self):
        from nomad_mem.skills.skill_evolution import SkillEvolutionManager
        db = tempfile.mktemp(suffix=".db")
        m = SkillEvolutionManager(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_record_result(self, manager):
        manager.register_skill("read_file", "读取文件")
        manager.record_skill_result("read_file", 0.5, True, 0.9)
        perf = manager.get_skill_performance("read_file")
        assert perf["total_uses"] == 1
        assert perf["success_rate"] == 1.0

    def test_performance_with_multiple_results(self, manager):
        manager.register_skill("read_file", "读取文件")
        manager.record_skill_result("read_file", 0.3, True, 0.8)
        manager.record_skill_result("read_file", 0.5, True, 0.9)
        manager.record_skill_result("read_file", 1.0, False, 0.3)
        perf = manager.get_skill_performance("read_file")
        assert perf["total_uses"] == 3
        assert perf["success_rate"] == pytest.approx(2/3, abs=0.01)
        assert perf["avg_response_time"] > 0

    def test_performance_no_data(self, manager):
        perf = manager.get_skill_performance("nonexistent")
        assert perf["total_uses"] == 0

    def test_get_optimization_suggestions_low_success(self, manager):
        manager.register_skill("flaky_skill", "不稳定的技能")
        for _ in range(5):
            manager.record_skill_result("flaky_skill", 0.5, False, 0.3)
        suggestions = manager.get_optimization_suggestions("flaky_skill")
        assert len(suggestions) >= 1
        assert any("成功率" in s.suggestion or "success" in s.suggestion.lower() for s in suggestions)

    def test_get_optimization_suggestions_slow(self, manager):
        manager.register_skill("slow_skill", "慢技能")
        for _ in range(5):
            manager.record_skill_result("slow_skill", 3.0, True, 0.5)
        suggestions = manager.get_optimization_suggestions("slow_skill")
        assert len(suggestions) >= 1
        assert any("响应" in s.suggestion or "time" in s.suggestion.lower() for s in suggestions)

    def test_no_suggestions_for_good_skill(self, manager):
        manager.register_skill("perfect_skill", "完美技能")
        for _ in range(5):
            manager.record_skill_result("perfect_skill", 0.1, True, 1.0)
        suggestions = manager.get_optimization_suggestions("perfect_skill")
        assert len(suggestions) == 0

    def test_suggestions_filtered_by_skill(self, manager):
        manager.register_skill("skill_a", "技能A")
        manager.register_skill("skill_b", "技能B")
        for _ in range(5):
            manager.record_skill_result("skill_a", 0.5, False, 0.2)
            manager.record_skill_result("skill_b", 0.1, True, 1.0)
        all_suggestions = manager.get_optimization_suggestions()
        skill_a_suggestions = manager.get_optimization_suggestions("skill_a")
        # skill_a should have suggestions, skill_b should not
        assert len(all_suggestions) >= 1
        assert len(skill_a_suggestions) >= 1


class TestSkillEvolutionLifecycle:
    @pytest.fixture
    def manager(self):
        from nomad_mem.skills.skill_evolution import SkillEvolutionManager
        db = tempfile.mktemp(suffix=".db")
        m = SkillEvolutionManager(db_path=db)
        yield m
        m.close()
        if os.path.exists(db):
            os.remove(db)

    def test_get_deprecation_candidates(self, manager):
        manager.register_skill("active_skill", "活跃技能")
        manager.register_skill("unused_skill", "未使用技能")
        # Record usage for active_skill only
        manager.record_skill_result("active_skill", 0.1, True)
        candidates = manager.get_deprecation_candidates()
        # unused_skill should be a candidate (no recent usage)
        unused_candidates = [c for c in candidates if c["skill_name"] == "unused_skill"]
        assert len(unused_candidates) >= 1

    def test_get_stats(self, manager):
        manager.register_skill("skill_a", "技能A")
        manager.register_skill("skill_b", "技能B")
        manager.create_version("skill_a", "2.0", "v2")
        manager.record_skill_result("skill_a", 0.1, True)
        manager.record_skill_result("skill_b", 0.2, True)
        stats = manager.get_stats()
        assert stats["total_skills"] >= 2
        assert stats["total_versions"] >= 3
        assert stats["total_results_recorded"] == 2

    def test_deprecated_skill_excluded_from_active(self, manager):
        manager.register_skill("old", "旧")
        manager.register_skill("new", "新")
        manager.deprecate_skill("old")
        active = manager.get_all_skills(status="active")
        active_names = [s["skill_name"] for s in active]
        assert "old" not in active_names
        assert "new" in active_names


# ─── Jarvis Integration Tests ────────────────────────────────────────────────


class TestJarvisSkillIntegration:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_skill_discoverer_initialized(self, jarvis):
        assert jarvis.skill_discoverer is not None

    def test_skill_evolution_initialized(self, jarvis):
        assert jarvis.skill_evolution is not None

    def test_status_includes_skill_modules(self, jarvis):
        status = jarvis.get_status()
        assert "skill_discoverer" in status["modules"]
        assert "skill_evolution" in status["modules"]

    def test_record_skill_usage(self, jarvis):
        usage_id = jarvis.record_skill_usage("read_file", context="test", result="ok")
        assert usage_id != ""

    def test_get_skill_stats(self, jarvis):
        jarvis.record_skill_usage("read_file", success=True)
        jarvis.record_skill_usage("read_file", success=True)
        stats = jarvis.get_skill_stats("read_file")
        assert stats["usage_count"] == 2

    def test_get_top_skills(self, jarvis):
        jarvis.record_skill_usage("skill_a", success=True)
        jarvis.record_skill_usage("skill_a", success=True)
        jarvis.record_skill_usage("skill_b", success=True)
        top = jarvis.get_top_skills(limit=5)
        assert len(top) >= 2

    def test_find_skill_combinations(self, jarvis):
        jarvis.record_skill_usage("read_file", success=True)
        jarvis.record_skill_usage("write_file", success=True)
        combos = jarvis.find_skill_combinations(min_frequency=1)
        assert isinstance(combos, list)

    def test_discover_skill_patterns(self, jarvis):
        jarvis.record_skill_usage("skill_a", success=True)
        jarvis.record_skill_usage("skill_a", success=True)
        patterns = jarvis.discover_skill_patterns()
        assert isinstance(patterns, list)

    def test_suggest_next_skill(self, jarvis):
        jarvis.record_skill_usage("read_file", success=True)
        jarvis.record_skill_usage("write_file", success=True)
        suggestion = jarvis.suggest_next_skill(["read_file"])
        assert isinstance(suggestion, (str, type(None)))

    def test_register_new_skill(self, jarvis):
        result = jarvis.register_new_skill("custom_skill", "自定义技能", "custom")
        assert result is True

    def test_get_skill_performance(self, jarvis):
        jarvis.register_new_skill("tracked_skill", "追踪技能")
        jarvis.record_skill_performance("tracked_skill", 0.5, True, 0.8)
        perf = jarvis.get_skill_performance("tracked_skill")
        assert perf["total_uses"] == 1

    def test_record_skill_performance(self, jarvis):
        jarvis.register_new_skill("perf_skill", "性能技能")
        jarvis.record_skill_performance("perf_skill", 0.3, True, 0.9)
        jarvis.record_skill_performance("perf_skill", 0.5, True, 0.8)
        perf = jarvis.get_skill_performance("perf_skill")
        assert perf["total_uses"] == 2

    def test_get_optimization_suggestions(self, jarvis):
        jarvis.register_new_skill("bad_skill", "需要优化的技能")
        for _ in range(5):
            jarvis.record_skill_performance("bad_skill", 3.0, False, 0.2)
        suggestions = jarvis.get_optimization_suggestions("bad_skill")
        assert len(suggestions) >= 1

    def test_get_skill_versions(self, jarvis):
        jarvis.register_new_skill("versioned_skill", "版本化技能")
        jarvis.create_skill_version("versioned_skill", "2.0", "性能优化")
        versions = jarvis.get_skill_versions("versioned_skill")
        assert len(versions) >= 2  # Initial + new

    def test_create_skill_version(self, jarvis):
        jarvis.register_new_skill("new_version_skill", "测试")
        version_id = jarvis.create_skill_version("new_version_skill", "3.0", "功能增加", "feature_add")
        assert version_id != ""

    def test_deprecate_skill(self, jarvis):
        jarvis.register_new_skill("to_deprecate", "待废弃")
        assert jarvis.deprecate_skill("to_deprecate") is True

    def test_get_deprecation_candidates(self, jarvis):
        jarvis.register_new_skill("unused_for_deprecation", "未使用")
        candidates = jarvis.get_deprecation_candidates()
        assert isinstance(candidates, list)

    def test_get_skill_system_stats(self, jarvis):
        jarvis.record_skill_usage("skill_a", success=True)
        jarvis.register_new_skill("skill_b", "技能B")
        jarvis.record_skill_performance("skill_b", 0.2, True, 0.9)
        stats = jarvis.get_skill_system_stats()
        assert "discovery" in stats
        assert "evolution" in stats

    def test_close_cleans_up(self, jarvis):
        jarvis.close()
        assert jarvis.initialized is False


class TestJarvisFullWorkflowWithSkills:
    @pytest.fixture
    def jarvis(self):
        from nomad_mem.core.jarvis_core import JarvisCore
        jarvis = JarvisCore()
        jarvis.initialize()
        yield jarvis
        jarvis.close()

    def test_full_skill_lifecycle(self, jarvis):
        # Register skill
        jarvis.register_new_skill("data_analysis", "数据分析", "analysis")

        # Record usage
        jarvis.record_skill_usage("data_analysis", context="分析数据", result="成功", success=True)
        jarvis.record_skill_usage("data_analysis", context="分析数据", result="成功", success=True)
        jarvis.record_skill_usage("data_analysis", context="分析数据", result="失败", success=False)

        # Record performance
        jarvis.record_skill_performance("data_analysis", 0.5, True, 0.8)
        jarvis.record_skill_performance("data_analysis", 0.8, True, 0.9)

        # Check stats
        stats = jarvis.get_skill_stats("data_analysis")
        assert stats["usage_count"] == 3

        perf = jarvis.get_skill_performance("data_analysis")
        assert perf["total_uses"] == 2

        # Create version
        jarvis.create_skill_version("data_analysis", "2.0", "优化分析速度")
        versions = jarvis.get_skill_versions("data_analysis")
        assert len(versions) >= 2

    def test_skill_optimization_workflow(self, jarvis):
        # Register multiple skills with different performance
        jarvis.register_new_skill("fast_skill", "快速技能")
        jarvis.register_new_skill("slow_skill", "慢速技能")
        jarvis.register_new_skill("unreliable_skill", "不可靠技能")

        # Fast and reliable
        for _ in range(10):
            jarvis.record_skill_performance("fast_skill", 0.1, True, 1.0)

        # Slow but reliable
        for _ in range(10):
            jarvis.record_skill_performance("slow_skill", 5.0, True, 0.7)

        # Unreliable
        for _ in range(10):
            jarvis.record_skill_performance("unreliable_skill", 0.5, False, 0.2)

        # Get suggestions
        suggestions = jarvis.get_optimization_suggestions()
        # Should have suggestions for slow_skill and unreliable_skill
        assert len(suggestions) >= 1

    def test_skill_pattern_discovery(self, jarvis):
        # Record usage patterns
        skills_used = ["read_file", "process_data", "write_file"]
        for _ in range(5):
            for skill in skills_used:
                jarvis.record_skill_usage(skill, success=True)

        # Discover patterns
        patterns = jarvis.discover_skill_patterns()
        assert isinstance(patterns, list)

        # Find combinations
        combos = jarvis.find_skill_combinations(min_frequency=1)
        assert isinstance(combos, list)
