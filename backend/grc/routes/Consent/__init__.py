"""
Consent Management Module
"""
from .consent_views import (
    get_consent_configurations,
    update_consent_configuration,
    bulk_update_consent_configurations,
    check_consent_required,
    record_consent_acceptance,
    get_user_consent_history,
    get_all_consent_acceptances
)
from .consent_decorator import require_consent, check_consent_programmatically

__all__ = [
    'get_consent_configurations',
    'update_consent_configuration',
    'bulk_update_consent_configurations',
    'check_consent_required',
    'record_consent_acceptance',
    'get_user_consent_history',
    'get_all_consent_acceptances',
    'require_consent',
    'check_consent_programmatically'
]

