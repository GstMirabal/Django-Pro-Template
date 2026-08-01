"""Operational views for the core app."""

import logging

from django.core.cache import cache
from django.db import connections
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

_HTTP_OK = 200
_HTTP_SERVICE_UNAVAILABLE = 503


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Report whether the critical dependencies are reachable.

    Each dependency is probed independently, so one failing subsystem degrades
    the response without masking the state of the other. Plain Django rather
    than a framework view: this project ships no REST framework, and a liveness
    probe is not a reason to add one.

    Args:
        request (HttpRequest): The incoming request. Unused; the probe takes no
            parameters.

    Returns:
        JsonResponse: A status map per dependency plus an aggregate ``system``
            verdict. ``200`` when every probe succeeds, ``503`` as soon as one
            fails.
    """
    report = {'database': 'OK', 'cache': 'OK', 'system': 'HEALTHY'}
    status_code = _HTTP_OK

    try:
        connections['default'].cursor()
    except Exception as exc:  # noqa: BLE001 - any driver error means DOWN
        logger.error('HealthCheck: database is DOWN: %s', exc)
        report['database'] = 'DOWN'
        report['system'] = 'DEGRADED'
        status_code = _HTTP_SERVICE_UNAVAILABLE

    try:
        cache.set('health_check', 'alive', timeout=5)
        if cache.get('health_check') != 'alive':
            msg = 'cache set/get round-trip failed'
            raise ValueError(msg)
    except Exception as exc:  # noqa: BLE001 - any backend error means DOWN
        logger.error('HealthCheck: cache is DOWN: %s', exc)
        report['cache'] = 'DOWN'
        report['system'] = 'DEGRADED'
        status_code = _HTTP_SERVICE_UNAVAILABLE

    return JsonResponse(report, status=status_code)
