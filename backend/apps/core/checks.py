"""Custom system checks for defects Django's own checks do not catch.

Django validates a ``ModelAdmin``'s ``fields``/``fieldsets`` only partially, and
``InlineModelAdmin.fields`` escapes that validation entirely: naming a field
that does not exist on the inline's model passes ``manage.py check`` cleanly and
fails only at request time, as a 500 on the change page.

This module closes that gap by constructing every registered admin form and
inline formset at check time — the same operation the admin performs when
rendering — so the failure surfaces before the process serves traffic.
"""

from collections.abc import Callable

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
from django.core.checks import CheckMessage, Error, Tags, register
from django.core.checks import Warning as CheckWarning
from django.core.exceptions import FieldError


class _CheckUser:
    """Permission-granting stand-in used to build admin forms during checks.

    Checks run before any request and must not touch the database, so a real
    user cannot be loaded. This object answers every permission query
    affirmatively, which is what the form-construction path needs to proceed.
    """

    is_active = True
    is_staff = True
    is_superuser = True
    is_authenticated = True

    def has_perm(self, *args: object, **kwargs: object) -> bool:  # noqa: ARG002
        return True

    def has_perms(self, *args: object, **kwargs: object) -> bool:  # noqa: ARG002
        return True

    def has_module_perms(self, *args: object, **kwargs: object) -> bool:  # noqa: ARG002
        return True


class _CheckRequest:
    """Minimal request stub carrying only what form construction reads."""

    method = 'GET'

    def __init__(self) -> None:
        self.user = _CheckUser()
        self.GET: dict[str, object] = {}
        self.POST: dict[str, object] = {}
        self.META: dict[str, object] = {}


def _label(model_admin: ModelAdmin | InlineModelAdmin) -> str:
    """Return a dotted import path identifying an admin class in messages.

    Args:
        model_admin (ModelAdmin | InlineModelAdmin): The admin instance.

    Returns:
        str: Its ``module.ClassName`` path.
    """
    cls = type(model_admin)
    return f'{cls.__module__}.{cls.__qualname__}'


def _check_one(
    model_admin: ModelAdmin | InlineModelAdmin,
    build: Callable[[], object],
    kind: str,
) -> list[CheckMessage]:
    """Run one form/formset construction and classify the outcome.

    Args:
        model_admin (ModelAdmin | InlineModelAdmin): The admin being verified.
        build (Callable[[], object]): Zero-argument callable performing the
            construction.
        kind (str): Either ``'form'`` or ``'formset'``, used in the message.

    Returns:
        list[CheckMessage]: Empty on success. A ``FieldError`` yields an
            ``Error``, because it is unambiguously a misconfiguration; any other
            exception yields a ``Warning``, since it may be an artefact of the
            request stub rather than a genuine defect.
    """
    try:
        build()
    except FieldError as exc:
        return [
            Error(
                f'{_label(model_admin)} declares a field that does not exist: {exc}',
                hint=(
                    "Check 'fields', 'fieldsets' and 'readonly_fields' against "
                    'the model this admin is bound to. A field belonging to a '
                    "related model must be declared on that model's own admin."
                ),
                obj=model_admin,
                id='core.E001',
            )
        ]
    except Exception as exc:  # noqa: BLE001 - reported, never propagated
        return [
            CheckWarning(
                f'{_label(model_admin)} {kind} could not be built during checks: '
                f'{type(exc).__name__}: {exc}',
                hint=(
                    "This may be a limitation of the check's request stub "
                    'rather than a real defect. Load the page in the admin to '
                    'confirm.'
                ),
                obj=model_admin,
                id='core.W001',
            )
        ]
    return []


@register(Tags.admin)
def check_admin_forms_are_constructible(
    app_configs: object = None,  # noqa: ARG001
    **kwargs: object,  # noqa: ARG001
) -> list[CheckMessage]:
    """Build every registered admin form and inline formset.

    Args:
        app_configs (object): Supplied by the check framework; unused, because
            the admin registry is global.
        **kwargs (object): Additional check-framework keywords.

    Returns:
        list[CheckMessage]: Every problem found across the admin registry.
    """
    request = _CheckRequest()
    messages: list[CheckMessage] = []

    for model_admin in admin.site._registry.values():  # noqa: SLF001
        messages += _check_one(
            model_admin, lambda ma=model_admin: ma.get_form(request), 'form'
        )

        for inline_class in getattr(model_admin, 'inlines', ()):
            inline = inline_class(model_admin.model, admin.site)
            messages += _check_one(
                inline, lambda i=inline: i.get_formset(request), 'formset'
            )

    return messages
