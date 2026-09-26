import json
from pathlib import Path


def load(path):
    text = Path(path).read_text(encoding='utf-8')
    try:
        import yaml
        cfg = yaml.safe_load(text)
    except ImportError:
        cfg = json.loads(text)  # shipped YAML uses the JSON subset
    m = cfg['mission']
    for k in ('search_spacing', 'search_altitude', 'search_speed', 'waypoint_tolerance',
              'state_timeout', 'feedback_timeout', 'mission_timeout', 'reinspection_timeout'):
        if m[k] <= 0:
            raise ValueError(f'mission.{k} must be positive')
    if m['search_min_x'] >= m['search_max_x'] or m['search_min_y'] >= m['search_max_y']:
        raise ValueError('Invalid search rectangle')
    if m['search_altitude'] < cfg['scene']['obstacle_ceiling'] + 3:
        raise ValueError('Search altitude must clear the tallest scene obstacle by >=3m')
    if not 0 <= cfg['perception']['confidence_threshold'] <= 1:
        raise ValueError('confidence_threshold must be in [0,1]')
    if abs(sum(cfg['triage']['weights'].values()) - 1) > 1e-8:
        raise ValueError('Triage weights must sum to one')
    cuts = cfg['triage']['thresholds']
    if not 1 >= cuts['P0'] > cuts['P1'] > cuts['P2'] > cuts['P3'] > 0:
        raise ValueError('Triage thresholds must descend P0..P3')
    return cfg
