from collections import OrderedDict

class LRUDict(OrderedDict):
    def __init__(self, max_size: int, *args, **kwargs):
        self.max_size = max_size
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)  
        super().__setitem__(key, value)
        if len(self) > self.max_size:
            self.popitem(last=False)
