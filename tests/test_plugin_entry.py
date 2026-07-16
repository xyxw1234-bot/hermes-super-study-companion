from pathlib import Path
import sys


def test_directory_plugin_entrypoint_loads_and_registers_all_tools():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("isolated_study_plugin", root / "__init__.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        class Context:
            def __init__(self): self.tools = []
            def register_tool(self, **kwargs): self.tools.append(kwargs)
            def register_command(self, *args, **kwargs): pass

        ctx = Context()
        module.register(ctx)
        assert {tool["name"] for tool in ctx.tools} == {
            "learning_start_diagnostic", "learning_issue_question", "learning_grade_answer",
            "learning_record_feynman", "learning_next_step", "learning_student_report",
        }
    finally:
        sys.path.remove(str(root))
