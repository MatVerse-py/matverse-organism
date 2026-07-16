from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_WORD = re.compile(r"[a-zA-ZÀ-ÿ0-9_-]{3,}")


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    description: str
    content: str
    source: Path


class SkillLibrary:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def discover(self) -> list[Skill]:
        candidates: set[Path] = set()
        agents = self.workspace / "AGENTS.md"
        if agents.is_file():
            candidates.add(agents)
        for root in (
            self.workspace / "skills",
            self.workspace / ".matverse" / "skills",
        ):
            if root.is_dir():
                candidates.update(root.rglob("*.md"))
        skills: list[Skill] = []
        for path in sorted(candidates):
            if path.stat().st_size > 1_000_000:
                continue
            content = path.read_text(encoding="utf-8", errors="replace").strip()
            if not content:
                continue
            name, description = self._metadata(path, content)
            skills.append(Skill(name, description, content, path))
        return skills

    def select(self, goal: str, max_skills: int = 5, max_chars: int = 30_000) -> list[Skill]:
        goal_terms = self._terms(goal)
        ranked: list[tuple[float, Skill]] = []
        for skill in self.discover():
            terms = self._terms(f"{skill.name} {skill.description} {skill.content[:4000]}")
            overlap = len(goal_terms & terms)
            union = len(goal_terms | terms) or 1
            score = overlap / union
            if skill.source.name == "AGENTS.md":
                score += 10.0
            ranked.append((score, skill))
        ranked.sort(key=lambda item: (-item[0], item[1].name.lower()))
        selected: list[Skill] = []
        used = 0
        for score, skill in ranked:
            if score <= 0 and skill.source.name != "AGENTS.md":
                continue
            if len(selected) >= max_skills:
                break
            remaining = max_chars - used
            if remaining <= 0:
                break
            content = skill.content[:remaining]
            selected.append(
                Skill(skill.name, skill.description, content, skill.source)
            )
            used += len(content)
        return selected

    @staticmethod
    def render(skills: list[Skill]) -> str:
        if not skills:
            return ""
        blocks = []
        for skill in skills:
            blocks.append(
                f"<skill name={skill.name!r} source={str(skill.source)!r}>\n"
                f"{skill.content}\n</skill>"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _metadata(path: Path, content: str) -> tuple[str, str]:
        name = path.stem
        description = ""
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                frontmatter = content[3:end]
                for line in frontmatter.splitlines():
                    key, separator, value = line.partition(":")
                    if not separator:
                        continue
                    if key.strip() == "name" and value.strip():
                        name = value.strip().strip("\"'")
                    if key.strip() == "description":
                        description = value.strip().strip("\"'")
        if not description:
            for line in content.splitlines():
                clean = line.strip("# ")
                if clean:
                    description = clean[:300]
                    break
        return name, description

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {word.casefold() for word in _WORD.findall(value)}
