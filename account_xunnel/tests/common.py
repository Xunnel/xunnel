def failed_requests_mock(*args, **kwargs):
    """Fallback for ``requests_mock.mock`` that raises a clear error when a decorated test runs."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            raise ImportError("The 'requests-mock' library is required to run this test")

        return wrapper

    return decorator
