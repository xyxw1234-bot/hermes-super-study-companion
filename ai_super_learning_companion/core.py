"""Deterministic learning core for the Hermes Super Study Companion.

The LLM teaches; this module owns evidence, grading, mastery, and review state.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


REVIEW_DAYS = {"memory": [1, 3, 7, 14, 30], "procedure": [1, 3, 7, 14], "concept": [3, 7, 14, 30], "design": [7, 14, 30]}
QUANTITATIVE_KINDS = {"memory", "procedure"}


@dataclass
class Objective:
    id: str
    name: str
    kind: str
    mastery_probability: float = 0.2
    qualitative_mastered: bool = False
    review_index: int = 0
    next_review_at: float | None = None


@dataclass
class State:
    student_id: str
    course_id: str
    subject: str
    curriculum_version: str
    objectives: list[Objective]
    attempts: list[dict[str, Any]] = field(default_factory=list)
    active_errors: list[dict[str, Any]] = field(default_factory=list)
    pending_question: dict[str, Any] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class LearningEngine:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path(self, student_id: str, course_id: str) -> Path:
        return self.root / student_id / f"{course_id}.json"

    def _save(self, state: State) -> None:
        state.updated_at = time.time()
        target = self._path(state.student_id, state.course_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self, student_id: str, course_id: str) -> State:
        target = self._path(student_id, course_id)
        if not target.exists():
            raise ValueError("学习档案不存在；请先开始诊断。")
        raw = json.loads(target.read_text(encoding="utf-8"))
        raw["objectives"] = [Objective(**item) for item in raw["objectives"]]
        return State(**raw)

    def start_diagnostic(self, student_id: str, course_id: str, subject: str, curriculum_version: str, objectives: list[dict[str, str]]) -> dict:
        normalized = []
        for item in objectives:
            kind = item.get("kind", "concept")
            if kind not in REVIEW_DAYS:
                raise ValueError("知识点类型仅支持 memory/procedure/concept/design")
            normalized.append(Objective(id=item["id"], name=item["name"], kind=kind))
        if not normalized:
            raise ValueError("至少需要一个知识点。")
        state = State(student_id=student_id, course_id=course_id, subject=subject, curriculum_version=curriculum_version, objectives=normalized)
        self._save(state)
        return self._public_state(state)

    def _mastered(self, objective: Objective) -> bool:
        return objective.qualitative_mastered if objective.kind not in QUANTITATIVE_KINDS else objective.mastery_probability >= 0.9

    def _next_step(self, state: State) -> dict:
        if state.pending_question:
            return {"action": "answer_pending", "objective_id": state.pending_question["objective_id"], "reason": "已有题目等待学生作答，必须先批改。"}
        now = time.time()
        due = [o for o in state.objectives if o.next_review_at is not None and o.next_review_at <= now]
        if due:
            chosen = sorted(due, key=lambda o: o.next_review_at or 0)[0]
            return {"action": "review", "objective_id": chosen.id, "objective_name": chosen.name, "reason": "该知识点到期复习。"}
        for objective in state.objectives:
            if self._mastered(objective):
                continue
            attempted = any(a["objective_id"] == objective.id for a in state.attempts)
            if objective.kind in QUANTITATIVE_KINDS:
                action = "practice" if attempted else "probe"
            else:
                action = "assess" if attempted else "probe"
            return {"action": action, "objective_id": objective.id, "objective_name": objective.name, "kind": objective.kind, "mastery_probability": round(objective.mastery_probability, 3), "reason": "未达到掌握门槛。"}
        return {"action": "complete", "reason": "所有知识点均有可追溯的掌握证据。"}

    def _public_state(self, state: State) -> dict:
        return {"student_id": state.student_id, "course_id": state.course_id, "subject": state.subject, "curriculum_version": state.curriculum_version, "next_step": self._next_step(state), "objectives": [{"id": o.id, "name": o.name, "kind": o.kind, "mastery_probability": round(o.mastery_probability, 3), "mastered": self._mastered(o), "next_review_at": o.next_review_at} for o in state.objectives]}

    def issue_question(self, student_id: str, course_id: str, objective_id: str, prompt: str, expected_answer: str, question_type: str = "short") -> dict:
        state = self._load(student_id, course_id)
        if state.pending_question:
            raise ValueError("已有待答题目，不能覆盖。")
        if not any(o.id == objective_id for o in state.objectives):
            raise ValueError("知识点不存在。")
        if not expected_answer.strip():
            raise ValueError("标准答案不能为空。")
        if question_type not in {"choice", "short", "open"}:
            raise ValueError("题型仅支持 choice/short/open")
        state.pending_question = {"id": f"q-{int(time.time() * 1000)}", "objective_id": objective_id, "prompt": prompt, "expected_answer": expected_answer, "question_type": question_type, "issued_at": time.time()}
        self._save(state)
        return {"question_id": state.pending_question["id"], "objective_id": objective_id, "prompt": prompt, "question_type": question_type}

    @staticmethod
    def _grade(answer: str, expected: str, question_type: str) -> bool:
        answer, expected = answer.strip().lower(), expected.strip().lower()
        if question_type == "choice":
            return answer.replace(" ", "") == expected.replace(" ", "")
        if question_type == "open":
            keys = [x.strip() for x in expected.replace("；", ";").replace("，", ",").replace("。", ",").split(",") if x.strip()]
            return bool(keys) and sum(key in answer for key in keys) / len(keys) >= 0.6
        return answer == expected or (len(expected) <= 30 and SequenceMatcher(None, answer, expected).ratio() >= 0.85)

    @staticmethod
    def _bkt_update(prior: float, is_correct: bool, slip: float = 0.1, guess: float = 0.2, transit: float = 0.15) -> float:
        if is_correct:
            observed = prior * (1 - slip) / (prior * (1 - slip) + (1 - prior) * guess)
        else:
            observed = prior * slip / (prior * slip + (1 - prior) * (1 - guess))
        return observed + (1 - observed) * transit

    def grade_pending_answer(self, student_id: str, course_id: str, answer: str) -> dict:
        state = self._load(student_id, course_id)
        pending = state.pending_question
        if not pending:
            raise ValueError("没有待批改题目。")
        objective = next(o for o in state.objectives if o.id == pending["objective_id"])
        correct = self._grade(answer, pending["expected_answer"], pending["question_type"])
        objective.mastery_probability = self._bkt_update(objective.mastery_probability, correct)
        interval = REVIEW_DAYS[objective.kind][min(objective.review_index, len(REVIEW_DAYS[objective.kind]) - 1)]
        if correct:
            objective.review_index += 1
        else:
            objective.review_index = max(0, objective.review_index - 1)
            state.active_errors.append({"question_id": pending["id"], "objective_id": objective.id, "error_type": "application" if answer.strip() else "metacognitive", "student_answer": answer, "created_at": time.time()})
        objective.next_review_at = time.time() + interval * 86400
        state.attempts.append({"question_id": pending["id"], "objective_id": objective.id, "is_correct": correct, "answered_at": time.time()})
        state.pending_question = None
        self._save(state)
        return {"is_correct": correct, "mastery_probability": round(objective.mastery_probability, 4), "error_type": None if correct else state.active_errors[-1]["error_type"], "review_due_at": objective.next_review_at, "active_errors": state.active_errors, "next_step": self._next_step(state)}

    def record_feynman_assessment(self, student_id: str, course_id: str, objective_id: str, passed: bool, evidence: str) -> dict:
        state = self._load(student_id, course_id)
        objective = next((o for o in state.objectives if o.id == objective_id), None)
        if not objective or objective.kind in QUANTITATIVE_KINDS:
            raise ValueError("费曼检查只适用于 concept/design 知识点。")
        objective.qualitative_mastered = bool(passed)
        state.attempts.append({"question_id": "feynman", "objective_id": objective_id, "is_correct": bool(passed), "evidence": evidence, "answered_at": time.time()})
        self._save(state)
        return self._public_state(state)

    def next_step(self, student_id: str, course_id: str) -> dict:
        return self._public_state(self._load(student_id, course_id))["next_step"]

    def student_report(self, student_id: str, course_id: str) -> dict:
        state = self._load(student_id, course_id)
        public = self._public_state(state)
        public["attempt_count"] = len(state.attempts)
        public["active_error_count"] = len(state.active_errors)
        return public
