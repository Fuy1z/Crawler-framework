from abc import ABCMeta

class Field(dict):
    pass


class ItemMeta(ABCMeta):
    def __new__(mcs, name, bases, attrs):
        field = {}
        cls_attr = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                field[key] = value
            else:
                cls_attr[key] = value
        cls_instance = super().__new__(mcs, name, bases, cls_attr)
        cls_instance.FIELDS = field
        return cls_instance