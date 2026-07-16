"""Hermes plugin registration for the AI Super Study Companion."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .core import LearningEngine


def _engine() -> LearningEngine:
    return LearningEngine(Path(os.getenv("HERMES_STUDY_DATA_DIR", "~/.hermes/study-companion")).expanduser())


def _handle_start(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().start_diagnostic(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_issue(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().issue_question(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_grade(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().grade_pending_answer(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_feynman(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().record_feynman_assessment(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_next(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().next_step(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_report(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().student_report(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_generate_material(args: dict, **kwargs) -> str:
    try:
        output_dir = Path(os.getenv("HERMES_STUDY_MATERIAL_DIR", "~/.hermes/study-materials")).expanduser()
        return json.dumps(_engine().generate_material(args["student_id"], args["course_id"], output_dir), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _handle_material_event(args: dict, **kwargs) -> str:
    try:
        return json.dumps(_engine().record_material_event(**args), ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"name": name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}


_ID = {"type": "string", "description": "稳定且去标识化的学生标识。"}
_COURSE = {"type": "string", "description": "课程或教材版本标识。"}

TOOLS = [
    ("learning_start_diagnostic", _schema("learning_start_diagnostic", "为学生创建可审计的课程知识点地图。仅在明确开始一个学习单元时调用。", {"student_id": _ID, "course_id": _COURSE, "subject": {"type": "string"}, "curriculum_version": {"type": "string"}, "objectives": {"type": "array", "description": "按学习顺序的知识点。", "items": {"type": "object"}}}, ["student_id", "course_id", "subject", "curriculum_version", "objectives"]), _handle_start),
    ("learning_issue_question", _schema("learning_issue_question", "登记一道题并安全保存标准答案；返回内容绝不包含标准答案。学生答题前必须调用。", {"student_id": _ID, "course_id": _COURSE, "objective_id": {"type": "string"}, "prompt": {"type": "string"}, "expected_answer": {"type": "string", "description": "仅存入学习内核，禁止在回复中展示。"}, "question_type": {"type": "string", "enum": ["choice", "short", "open"]}}, ["student_id", "course_id", "objective_id", "prompt", "expected_answer"]), _handle_issue),
    ("learning_grade_answer", _schema("learning_grade_answer", "批改当前待答题，更新 BKT 掌握度、错因记录和复习计划。学生作答后立即调用。", {"student_id": _ID, "course_id": _COURSE, "answer": {"type": "string"}}, ["student_id", "course_id", "answer"]), _handle_grade),
    ("learning_record_feynman", _schema("learning_record_feynman", "记录概念/设计类知识点的费曼式解释检查。不能无证据判通过。", {"student_id": _ID, "course_id": _COURSE, "objective_id": {"type": "string"}, "passed": {"type": "boolean"}, "evidence": {"type": "string"}}, ["student_id", "course_id", "objective_id", "passed", "evidence"]), _handle_feynman),
    ("learning_next_step", _schema("learning_next_step", "读取学习内核决定的下一步；每轮辅导先调用，禁止模型自行跳过知识点。", {"student_id": _ID, "course_id": _COURSE}, ["student_id", "course_id"]), _handle_next),
    ("learning_student_report", _schema("learning_student_report", "返回可解释学习报告、掌握证据与当前错因数量；不返回标准答案。", {"student_id": _ID, "course_id": _COURSE}, ["student_id", "course_id"]), _handle_report),
    ("learning_generate_material", _schema("learning_generate_material", "按当前知识点、错因与掌握度生成真实互动 H5 学习素材。只在已有学习档案后调用。", {"student_id": _ID, "course_id": _COURSE}, ["student_id", "course_id"]), _handle_generate_material),
    ("learning_record_material_event", _schema("learning_record_material_event", "接收已生成互动素材的学生行为事件，回写掌握度与错因。答对/答错必须携带页面产生的作答证据。", {"student_id": _ID, "course_id": _COURSE, "artifact_id": {"type": "string"}, "event": {"type": "string", "enum": ["question_correct", "question_wrong", "hint_requested", "material_completed"]}, "objective_id": {"type": "string"}, "evidence": {"type": "string", "description": "页面选择、作答或提示请求产生的可追溯证据；答对/答错时必填。"}}, ["student_id", "course_id", "artifact_id", "event", "objective_id"]), _handle_material_event),
]


def register(ctx) -> None:
    for name, schema, handler in TOOLS:
        ctx.register_tool(name=name, toolset="study_companion", schema=schema, handler=handler, emoji="📚")
    ctx.register_command("学习报告", lambda raw: "请让我先读取你的学习档案后生成报告。", description="查看当前学习报告")
