from pathlib import Path
from ai_super_learning_companion.core import LearningEngine


def engine(tmp_path, kind="procedure"):
    e = LearningEngine(tmp_path / "state")
    e.start_diagnostic("s", "c", "数学", "人教版", [{"id": "o", "name": "有理数加法", "kind": kind}])
    return e


def test_h5_generation_and_event_backwrite(tmp_path):
    e = engine(tmp_path)
    material = e.generate_material("s", "c", tmp_path / "materials")
    html = Path(material["path"]).read_text(encoding="utf-8")
    assert material["kind"] == "interactive-practice"
    assert "<button" in html and "postMessage" in html and "aria-live" in html
    before = e.student_report("s", "c")["objectives"][0]["mastery_probability"]
    result = e.record_material_event("s", "c", material["artifact_id"], "question_correct", "o", evidence="学生选择先分析条件")
    after = e.student_report("s", "c")["objectives"][0]["mastery_probability"]
    assert result["accepted"] and after > before


def test_error_routes_to_game_and_requires_bound_objective(tmp_path):
    e = engine(tmp_path)
    e.issue_question("s", "c", "o", "-2+5=?", "3")
    e.grade_pending_answer("s", "c", "2")
    material = e.generate_material("s", "c", tmp_path / "materials")
    assert material["kind"] == "error-repair-game"
    try:
        e.record_material_event("s", "c", material["artifact_id"], "question_wrong", "other", evidence="x")
    except ValueError:
        pass
    else:
        raise AssertionError("cross-objective event must be rejected")


def test_plugin_registers_v02_material_tools():
    import ai_super_learning_companion as plugin
    class C:
        def __init__(self): self.tools = []
        def register_tool(self, **kw): self.tools.append(kw)
        def register_command(self, *args, **kw): pass
        def register_skill(self, *args, **kw): pass
    c = C()
    plugin.register(c)
    assert {"learning_generate_material", "learning_record_material_event"} <= {x["name"] for x in c.tools}
