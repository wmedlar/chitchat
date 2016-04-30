from . import utils


def command(trigger, case_sensitive=False):
    
    try:
        lower_trigger = trigger.casefold()
        
    except AttributeError:
        lower_trigger = trigger
        
    def func(arg):
        
        try:
            first = arg.split()[0]
            
        except (AttributeError, ValueError):
            first = arg
            
        if case_sensitive:
            return trigger == first
        
        try:
            lower_first = first.casefold()
        
        except AttributeError:
            lower_first = first
            
        return lower_trigger == lower_first
    
    return func


def contains(item, case_sensitive=False):
    
    try:
        lower_item = item.casefold()
    
    except AttributeError:
        lower_item = item
    
    def func(iterable):
        
        if case_sensitive:
            return item in iterable
        
        lower_iter = utils.casefold_each(iterable)
        
        return lower_item in lower_iter
    
    doc = 'Tests for case-{0}sensitive containment of {1!r}.'
    func.__doc__ = doc.format('' if case_sensitive else 'in', item)
    
    rep = 'contains(item={0}, case_sensitive={1})'
    func.__repr__ = lambda self: rep.format(item, case_sensitive)
    
    return func


def contained_in(iterable, case_sensitive=False):
    """
    Creates a function that accepts one argument and returns whether that argument is
    contained within `a`.
    
    >>> isvowel = contained_in(['a', 'e', 'i', 'o', 'u'])
    >>> isvowel('y')
    False
    >>> isvowel('A')
    True
    
    args:
        a: iterable containing values of any type for comparison
        case_sensitive: bool; if False this will attempt to call str.casefold on each
                        item in `a` and the argument passed to the returned function
                        before containment comparison
    
    returns:
        function of one argument for containment testing in `a`
        
    """
    
    lower_iter = utils.casefold_each(iterable)
    
    def func(item):
    
        if case_sensitive:
            return item in iterable
        
        try:
            lower_item = item.casefold()
        
        except AttributeError:
            lower_item = item
            
        return lower_item in lower_iter
    
    doc = 'Tests for case-{0}sensitive containment within {1!r}.'
    func.__doc__ = doc.format('' if case_sensitive else 'in', iterable)
    
    rep = 'contained_in(iterable={0}, case_sensitive={1})'
    func.__repr__ = lambda self: rep.format(iterable, case_sensitive)
    
    return func