"""
BridgeConfig: rdf-bridge-config.yaml 로더

탐색 순서:
  1. 명시적 경로 (config_path 인자)
  2. BRIDGE_DIR/rdf-bridge-config.yaml  (패키지 루트)
  3. cwd/rdf-bridge-config.yaml
  4. 없으면 기본값(빈 맵 + generic 네임스페이스) 반환

rdf-bridge-config.yaml 포맷:
  namespace_base: "http://your-project.io/"
  entity_types:
    - name: MyType
      layer: semantic          # optional (default: "general")
      dir: MyType              # optional (default: name)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class EntityTypeEntry:
    name:  str
    layer: str = "general"
    dir:   str = ""

    def __post_init__(self):
        if not self.dir:
            self.dir = self.name


@dataclass
class BridgeConfig:
    namespace_base: str                    = "http://rdf-bridge.local/"
    entity_types:   list[EntityTypeEntry]  = field(default_factory=list)

    # ── 빌드된 룩업 테이블 ────────────────────────────────────────────────────
    @property
    def layer_map(self) -> dict[str, str]:
        return {e.name: e.layer for e in self.entity_types}

    @property
    def dir_map(self) -> dict[str, str]:
        return {e.name: e.dir for e in self.entity_types}

    # ── 팩토리 ───────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, config_path: Path | None = None) -> "BridgeConfig":
        path = cls._find_config(config_path)
        if path is None:
            return cls()

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        entity_types = [
            EntityTypeEntry(**{k: v for k, v in et.items() if k in ("name", "layer", "dir")})
            for et in data.get("entity_types", [])
        ]
        return cls(
            namespace_base=data.get("namespace_base", "http://rdf-bridge.local/"),
            entity_types=entity_types,
        )

    @staticmethod
    def _find_config(explicit: Path | None) -> Path | None:
        if explicit:
            return explicit if explicit.exists() else None

        candidates = [
            # 패키지 루트 (core/ 의 부모)
            Path(__file__).parent.parent / "rdf-bridge-config.yaml",
            # 현재 작업 디렉토리
            Path.cwd() / "rdf-bridge-config.yaml",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None


# ── 모듈 레벨 싱글턴 (최초 import 시 로드) ────────────────────────────────────
_config: BridgeConfig | None = None


def get_config(config_path: Path | None = None) -> BridgeConfig:
    """싱글턴 BridgeConfig 반환. 최초 호출 시 파일에서 로드."""
    global _config
    if _config is None or config_path is not None:
        _config = BridgeConfig.load(config_path)
    return _config
