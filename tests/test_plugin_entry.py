from pathlib import Path
import sys


def test_directory_plugin_entrypoint_loads_and_registers_all_tools_and_skill():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("isolated_study_plugin", root / "__init__.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class Context:
            def __init__(self):
                self.tools = []
                self.skills = []
            def register_tool(self, **kwargs): self.tools.append(kwargs)
            def register_command(self, *args, **kwargs): pass
            def register_skill(self, *args, **kwargs): self.skills.append((args, kwargs))

        ctx = Context()
        module.register(ctx)
        assert {tool["name"] for tool in ctx.tools} == {
            "learning_start_diagnostic", "learning_issue_question", "learning_grade_answer",
            "learning_record_feynman", "learning_next_step", "learning_student_report",
            "learning_generate_material", "learning_record_material_event",
        }
        assert ctx.skills[0][0][0] == "ai-super-learning-companion"
        assert ctx.skills[0][0][1].name == "SKILL.md"
    finally:
        sys.path.remove(str(root))
