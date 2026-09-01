from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PipelineInfo:
    name: str
    group: str
    description: str
    func: Callable[..., Any]


_REGISTRY: dict[str, PipelineInfo] = {}


def register(name: str, group: str, description: str = "") -> Callable:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if name in _REGISTRY:
            raise ValueError(f"Pipeline duplicado: {name}")
        _REGISTRY[name] = PipelineInfo(name=name, group=group, description=description, func=func)
        return func

    return decorator


def get_pipeline(name: str) -> PipelineInfo:
    if name not in _REGISTRY:
        raise KeyError(f"No existe el pipeline '{name}'. Usá 'ch list' para verlos.")
    return _REGISTRY[name]


def all_pipelines() -> list[PipelineInfo]:
    return sorted(_REGISTRY.values(), key=lambda p: (p.group, p.name))
