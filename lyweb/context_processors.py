def browser(request):
    """
    Adds browser context variables to the context.

    """

    # For IE6
    if request.META.get('HTTP_USER_AGENT', '').find('MSIE 6.0') != -1:
        return {'BROWSER': 'IE6'}
    else:
        return {'BROWSER': 'NORMAL'}
