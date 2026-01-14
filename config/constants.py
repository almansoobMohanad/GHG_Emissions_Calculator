from datetime import datetime

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

def get_reporting_periods():
    """
    Generate a list of years for reporting periods.
    Includes 10 past years, current year, and 2 future years.
    
    Returns:
        list: Years as strings in descending order (newest first)
    """
    current_year = datetime.now().year
    years = list(range(current_year - 10, current_year + 3))
    return [str(year) for year in sorted(years, reverse=True)]

REPORTING_PERIODS = get_reporting_periods()