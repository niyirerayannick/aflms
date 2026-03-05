from .models import SystemSettings


def system_settings(request):
    """Make system settings available to all templates"""
    try:
        settings = SystemSettings.get_settings()
    except Exception:
        settings = None
    
    # Define the color mapping
    color_map = {
        'blue': {
            'primary': 'blue',
            'bg': 'bg-blue-600',
            'bg_hover': 'hover:bg-blue-700',
            'bg_light': 'bg-blue-50',
            'text': 'text-blue-700',
            'ring': 'ring-blue-500',
            'border': 'border-blue-600',
        },
        'green': {
            'primary': 'green',
            'bg': 'bg-green-600',
            'bg_hover': 'hover:bg-green-700',
            'bg_light': 'bg-green-50',
            'text': 'text-green-700',
            'ring': 'ring-green-500',
            'border': 'border-green-600',
        },
        'purple': {
            'primary': 'purple',
            'bg': 'bg-purple-600',
            'bg_hover': 'hover:bg-purple-700',
            'bg_light': 'bg-purple-50',
            'text': 'text-purple-700',
            'ring': 'ring-purple-500',
            'border': 'border-purple-600',
        },
        'red': {
            'primary': 'red',
            'bg': 'bg-red-600',
            'bg_hover': 'hover:bg-red-700',
            'bg_light': 'bg-red-50',
            'text': 'text-red-700',
            'ring': 'ring-red-500',
            'border': 'border-red-600',
        },
        'orange': {
            'primary': 'orange',
            'bg': 'bg-orange-600',
            'bg_hover': 'hover:bg-orange-700',
            'bg_light': 'bg-orange-50',
            'text': 'text-orange-700',
            'ring': 'ring-orange-500',
            'border': 'border-orange-600',
        },
    }
    
    theme_color = 'blue'  # default
    currency_symbol = '$'
    currency_code = 'USD'
    
    if settings:
        theme_color = settings.primary_color or 'blue'
        currency_symbol = settings.currency_symbol or '$'
        currency_code = settings.currency or 'USD'
    
    return {
        'system_settings': settings,
        'theme': color_map.get(theme_color, color_map['blue']),
        'currency_symbol': currency_symbol,
        'currency_code': currency_code,
    }
