from .scene.scene_routes import scene_bp
from .prompt_routes import prompt_bp
# from .evaluate_routes import evaluate_bp
# from .dimension_routes import dimension_bp
from .progress_routes import progress_bp
from .realtime_routes import realtime_bp

__all__ = [
    "scene_bp",
    "prompt_bp",
    # "evaluate_bp",
    # "dimension_bp",
    "progress_bp",
    "realtime_bp",
]
