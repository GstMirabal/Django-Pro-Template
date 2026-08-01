# backend/apps/core/tests.py

"""Configuration and Sanity Tests for the Core App.

This file contains tests to verify that the project's foundational
configuration is correct and robust.
"""

import logging
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings

from apps.core.checks import check_admin_forms_are_constructible
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config.settings import _parse_strict_bool

User = get_user_model()


class ConfigurationSmokeTest(TestCase):
    """A simple smoke test to ensure the project can start and tests can run."""

    def test_settings_load_correctly(self) -> None:
        """Verify that settings are loaded without raising errors."""
        self.assertTrue(expr=True)


class DatabaseConnectionTest(TestCase):
    """Verifies the database configuration and active user model interaction."""

    def test_database_connection_and_user_model(self) -> None:
        """Verify database connectivity and the active user model integration.

        `AUTH_USER_MODEL` is intentionally left unset in this base template
        (see `settings.py` Section 8.1) — swapping in a custom user model is
        a decision each fork makes for itself, not something imposed here.
        `get_user_model()` resolves to whatever is actually active, so this
        test stays valid regardless of that decision.
        """
        try:
            user = User.objects.create_user(
                username='testuser', password='TestPassword123!'
            )
            self.assertIsNotNone(user)
        except Exception as e:  # noqa: BLE001
            self.fail(
                'User creation failed, indicating a problem with the DB '
                f'connection or the active user model setup. Original error: {e}'
            )


class SecurityHeadersRegressionTest(TestCase):
    """Regression guard for the security headers Django sets by default.

    `X-Frame-Options` and `X-Content-Type-Options` are Django's own global
    defaults (`django/conf/global_settings.py`), active in every environment
    regardless of this project's `if not DEBUG:` production-hardening block
    (`settings.py` Section 3) — so this test cannot meaningfully verify that
    block. The real verification of the production-only settings (SSL
    redirect, HSTS, CSP, secure cookies) runs in CI via
    `manage.py check --deploy` under a simulated `DEBUG=false` environment,
    which is the only way to honestly exercise settings computed once at
    module import time.
    """

    def test_default_security_headers_are_present(self) -> None:
        """Ensure Django's baseline security headers stay present."""
        response = self.client.get('/admin/login/', follow=True)

        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')


class ParseStrictBoolTest(TestCase):
    """Covers `_parse_strict_bool`, the guard behind the DEBUG boolean fix.

    `envtoml`/`toml` only cast a string to a TOML boolean when it is exactly
    `true`/`false` in lowercase; any other casing silently falls back to a
    non-empty (truthy) string. This helper is what stands between that
    footgun and `DEBUG`/`EMAIL_USE_TLS`/every other strict-boolean setting.
    """

    def test_accepts_true_case_insensitive(self) -> None:
        """Any casing of "true" parses to Python True."""
        for value in ('true', 'True', 'TRUE', 'tRuE'):
            with self.subTest(value=value):
                self.assertTrue(_parse_strict_bool(value, 'TEST_KEY'))

    def test_accepts_false_case_insensitive(self) -> None:
        """Any casing of "false" parses to Python False.

        This is the exact case that caused the original bug: envtoml turning
        a config value of "False" into a truthy Python string.
        """
        for value in ('false', 'False', 'FALSE', 'fAlSe'):
            with self.subTest(value=value):
                self.assertFalse(_parse_strict_bool(value, 'TEST_KEY'))

    def test_passes_through_an_already_resolved_bool(self) -> None:
        """A value envtoml already resolved to a real bool is returned as-is."""
        self.assertTrue(_parse_strict_bool(True, 'TEST_KEY'))  # noqa: FBT003
        self.assertFalse(_parse_strict_bool(False, 'TEST_KEY'))  # noqa: FBT003

    def test_rejects_unrecognized_values(self) -> None:
        """An unrecognized value fails loudly instead of guessing a default."""
        for value in ('nope', 'yes', '1', '', None):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                _parse_strict_bool(value, 'TEST_KEY')


class CrossOriginAuthConfigTest(TestCase):
    """Verifies the settings a decoupled frontend needs to authenticate.

    Session-based cross-origin authentication needs both of these — CORS
    alone does not imply either.
    """

    def test_csrf_trusted_origins_mirrors_cors_allowed_origins(self) -> None:
        """CSRF_TRUSTED_ORIGINS must match CORS_ALLOWED_ORIGINS.

        Otherwise a session-authenticated POST from an allowed frontend
        origin is rejected with a 403 regardless of CORS.
        """
        self.assertEqual(settings.CSRF_TRUSTED_ORIGINS, settings.CORS_ALLOWED_ORIGINS)

    def test_cors_allow_credentials_is_enabled(self) -> None:
        """CORS_ALLOW_CREDENTIALS must be enabled.

        Without it, the browser never sends/accepts the session cookie
        cross-origin in the first place, even with CSRF_TRUSTED_ORIGINS set.
        """
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)


class AxesLockoutTest(TestCase):
    """Functional test of the django-axes brute-force protection.

    Exercises the real login flow rather than just asserting a setting's
    value, so it would have caught AXES_LOCKOUT_PARAMETERS/
    AXES_RESET_ON_SUCCESS mistakes.
    """

    def test_admin_login_locks_out_after_failure_limit(self) -> None:
        """The (username, IP) pair locks out after AXES_FAILURE_LIMIT fails.

        The response becomes 429 instead of re-rendering the login form.
        """
        login_url = '/admin/login/'
        bad_credentials = {'username': 'nonexistent-user', 'password': 'wrong-password'}

        for attempt in range(settings.AXES_FAILURE_LIMIT - 1):
            response = self.client.post(login_url, bad_credentials)
            with self.subTest(attempt=attempt):
                self.assertEqual(response.status_code, 200)

        # The attempt that reaches AXES_FAILURE_LIMIT, and any after it, lock out.
        for attempt in range(2):
            response = self.client.post(login_url, bad_credentials)
            with self.subTest(post_limit_attempt=attempt):
                self.assertEqual(response.status_code, 429)

    def test_lockout_resets_after_successful_login(self) -> None:
        """AXES_RESET_ON_SUCCESS clears the failure count on a good login.

        Otherwise the count would linger for that (username, IP) pair.
        """
        User.objects.create_user(
            username='resettable-user', password='CorrectPassword123!', is_staff=True
        )
        bad_credentials = {'username': 'resettable-user', 'password': 'wrong-password'}

        # A few failures, well under the limit.
        for _ in range(settings.AXES_FAILURE_LIMIT - 2):
            self.client.post('/admin/login/', bad_credentials)

        good_response = self.client.post(
            '/admin/login/',
            {'username': 'resettable-user', 'password': 'CorrectPassword123!'},
        )
        self.assertNotEqual(good_response.status_code, 429)

        # Fresh failures after the successful login should not inherit the
        # earlier count — none of these alone should trip the lockout.
        for _ in range(settings.AXES_FAILURE_LIMIT - 1):
            response = self.client.post('/admin/login/', bad_credentials)
            self.assertNotEqual(response.status_code, 429)


class SecurityMiddlewareHeaderRegressionTest(TestCase):
    """Regression guard for two previously-silent settings-format bugs.

    django-csp's 4.0 config migration and PERMISSIONS_POLICY (vs the made-up
    SECURE_PERMISSIONS_POLICY) both failed silently — Django ignores setting
    keys it doesn't recognize, and the old CSP format only broke at process
    boot with DEBUG=false, which unit tests don't normally exercise.
    `override_settings` here tests the middleware/setting integration
    directly, independent of the `if not DEBUG:` branch in settings.py
    (which CI's `deploy-check` job verifies separately by actually booting
    with DEBUG=false).
    """

    @override_settings(
        CONTENT_SECURITY_POLICY={'DIRECTIVES': {'default-src': ["'self'"]}}
    )
    def test_csp_middleware_sends_the_configured_header(self) -> None:
        """Would have caught the django-csp 3.x/4.x format mismatch."""
        response = self.client.get('/admin/login/')
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertEqual(
            response.headers['Content-Security-Policy'], "default-src 'self'"
        )

    @override_settings(PERMISSIONS_POLICY={'geolocation': []})
    def test_permissions_policy_middleware_sends_the_configured_header(self) -> None:
        """Would have caught the SECURE_PERMISSIONS_POLICY dead-config bug.

        That setting name was never read by any installed package.
        """
        response = self.client.get('/admin/login/')
        self.assertIn('Permissions-Policy', response.headers)
        self.assertEqual(response.headers['Permissions-Policy'], 'geolocation=()')


class HealthCheckTest(TestCase):
    """The liveness probe must report per-dependency state, not just 200/500."""

    def test_reports_healthy_when_dependencies_are_reachable(self) -> None:
        """Verify a fully reachable stack yields 200 and a HEALTHY verdict."""
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'database': 'OK', 'cache': 'OK', 'system': 'HEALTHY'},
        )

    def test_reports_degraded_when_cache_round_trip_fails(self) -> None:
        """Verify an unreachable cache degrades the verdict and returns 503.

        Only the view's own reference is replaced: patching the shared cache
        would also break unrelated machinery that reads the same object.
        """

        class _DeadCache:
            """Cache double whose round-trip always fails."""

            def set(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
                """Raise as an unreachable backend would."""
                msg = 'cache backend unreachable'
                raise ConnectionError(msg)

            def get(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
                """Return nothing, as a missing entry would."""
                return None

        with patch('apps.core.views.cache', _DeadCache()):
            response = self.client.get('/health/')

        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body['cache'], 'DOWN')
        self.assertEqual(body['database'], 'OK')
        self.assertEqual(body['system'], 'DEGRADED')

    def test_rejects_non_get(self) -> None:
        """Verify the probe is read-only."""
        self.assertEqual(self.client.post('/health/').status_code, 405)


class ApplicationLoggingTest(TestCase):
    """Application loggers must reach a handler.

    LOGGING previously declared only 'django' and 'project', while every module
    calls getLogger(__name__) — yielding 'apps.*', 'config.*' and 'utils.*'.
    Those records matched no logger and were discarded in silence.
    """

    def _resolved_handlers(self, name: str) -> list[logging.Handler]:
        """Walk the logger hierarchy the way logging dispatches a record.

        Args:
            name (str): Dotted logger name.

        Returns:
            list[logging.Handler]: Every handler the record would reach.
        """
        handlers: list[logging.Handler] = []
        current: logging.Logger | None = logging.getLogger(name)
        while current:
            handlers.extend(current.handlers)
            current = current.parent if current.propagate else None
        return handlers

    def test_application_loggers_reach_a_handler(self) -> None:
        """Verify no application logger resolves to an empty handler list."""
        for name in ('apps.core.views', 'apps.core.validators', 'config.settings'):
            with self.subTest(logger=name):
                self.assertTrue(
                    self._resolved_handlers(name),
                    f'{name!r} resolves to no handler; its records are discarded',
                )


class AdminIntegrityCheckTest(TestCase):
    """core.E001 must catch a field declared on the wrong model.

    Django's own checks do not validate inline `fields`, so this class of
    defect reaches production as a 500 on the change page.
    """

    def test_registered_admins_build_cleanly(self) -> None:
        """Verify every registered admin form and inline formset constructs."""
        self.assertEqual(check_admin_forms_are_constructible(), [])

    def test_detects_a_field_that_does_not_exist(self) -> None:
        """Verify a field naming no model attribute produces core.E001."""

        class BrokenGroupAdmin(admin.ModelAdmin):
            """Admin declaring a field the model does not have."""

            fields = ('name', 'field_that_does_not_exist')

        original = admin.site._registry[Group]  # noqa: SLF001
        admin.site._registry[Group] = BrokenGroupAdmin(Group, admin.site)  # noqa: SLF001
        try:
            messages = check_admin_forms_are_constructible()
        finally:
            admin.site._registry[Group] = original  # noqa: SLF001

        self.assertTrue(any(m.id == 'core.E001' for m in messages))
