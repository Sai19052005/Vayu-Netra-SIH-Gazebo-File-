"""Engineering response-priority demonstration, not clinical triage."""
from .perception_interface import validate


def assess(observation, cfg):
    o = dict(validate(observation))
    context = o.get('context') or {}
    weights = cfg['triage']['weights']
    if any(context.get(k) is None for k in weights):
        return dict(o, priority='UNASSESSED', risk_score=None, priority_label='Context required')
    if any(not 0 <= context[k] <= 1 for k in weights):
        raise ValueError('Risk inputs must lie in [0,1]')
    score = sum(context[k]*weight for k, weight in weights.items())
    priority = next((p for p in ('P0','P1','P2','P3') if score >= cfg['triage']['thresholds'][p]), 'P4')
    labels = {'P0':'Critical','P1':'Very High','P2':'High','P3':'Moderate','P4':'Low / Monitor'}
    return dict(o, priority=priority, risk_score=score, priority_label=labels[priority],
                triage_basis='VAYU_NETRA_ENGINEERING_DEMONSTRATION_NOT_CLINICAL')
