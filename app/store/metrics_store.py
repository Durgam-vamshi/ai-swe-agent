# app/store/metrics_store.py

metrics = {
    "success_count": 0,
    "failure_count": 0,
    "no_change_count": 0,
    "retry_count": 0,
    "localized_fixes": 0
}


def increment_success():
    metrics["success_count"] += 1


def increment_failure():
    metrics["failure_count"] += 1


def increment_no_change():
    metrics["no_change_count"] += 1


def increment_retry():
    metrics["retry_count"] += 1


def increment_localized_fix():
    metrics["localized_fixes"] += 1


def get_metrics():
    return metrics