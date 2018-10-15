ERRORS_CODE = {
    'UNAUTHORIZED': {
        'code': 401,
        'message': 'Authorization failed with the provided credentials.'
    },
    'DOES_NOT_EXITS': {
        'code': 401,
        'message': 'The {obj} does exits in system.'
    },
    'MISSING_FIELD': {
        'code': 402,
        'message': 'Must provide field ``{field}`` when creating a {obj}.'
    },
    'DUPLICATE_VALUE': {
        'code': 403,
        'message': 'This {obj} is already exits. Please enter another one.'
    },
    'INVALID_PAGE': {
        'code': 404,
        'message': 'Sorry, no results on that page.'
    },
    'EMAIL_FAILED': {
        'code': 405,
        'message': 'Cannot send email.'
    },
    'INVALID_DATA': {
        'code': 406,
        'message': 'Data is not valid.'
    },
    'UNKNOWNERROR': {
        'code': 407,
        'message': 'Unknown error.'
    },
    'INVALID_OPERATOR': {
        'code': 408,
        'message': 'Client performed a invalid operation'
    }
}