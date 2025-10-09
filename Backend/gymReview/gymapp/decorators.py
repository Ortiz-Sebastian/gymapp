from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps
import time

def rate_limit(max_requests=100, window=3600, key_prefix='rl'):
    """
    Rate limiting decorator
    
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds (default: 1 hour)
        key_prefix: Prefix for cache key
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get client IP
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            
            # Create cache key
            cache_key = f"{key_prefix}:{client_ip}"
            
            # Get current request count
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= max_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.'
                }, status=429)
            
            # Increment counter
            cache.set(cache_key, current_requests + 1, window)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit_auth(max_requests=5, window=300):
    """
    Rate limiting for authentication endpoints (login, register, password reset)
    More restrictive than general rate limiting
    """
    return rate_limit(max_requests=max_requests, window=window, key_prefix='auth_rl')
