# User roles
ROLES = {
    'ADMIN': 'admin',
    'MANAGER': 'manager',
    'NORMAL_USER': 'normal_user'
}

# Company verification statuses
VERIFICATION_STATUS = {
    'PENDING': 'pending',
    'VERIFIED': 'verified',
    'REJECTED': 'rejected'
}

# Reporting periods - dynamically generated
from utils.date_utils import get_reporting_periods

REPORTING_PERIODS = get_reporting_periods()