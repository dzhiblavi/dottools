from pydoc import locate

from dots.config.ignored import IgnoredPathsManager


LIST_META_KEY = "_list"
FROM_META_KEY = "_from"


class _ObjectTree:
    def __init__(self, obj=None, parent=None):
        self._object = obj
        self._parent = parent

    def __str__(self):
        return str(self.get_object())

    def set_object(self, obj):
        self._object = obj

    def get_parent(self):
        return self._parent

    def get_object(self):
        return self._object


class _ObjectTreeDictAdapter(_ObjectTree):
    def __init__(self, obj=None, parent=None):
        super().__init__(obj, parent)

    def _assure_dict(self, method):
        assert isinstance(
            self.get_object(), dict
        ), f"{method}() called on an Object of type different from dict"

    def __contains__(self, key: str) -> bool:
        self._assure_dict("__contains__")
        return key in self.get_object()

    def _lift_raw_object(self, default):
        # Lift an object of unrelated type to the type of
        # the current object (this object will become a parent).
        if default is None:
            return default

        return type(self)(obj=default, parent=self)

    def _get_1(self, key: str):
        return self.get_object().get(key, None)

    def get(self, key: str, default=None):
        self._assure_dict("get")

        parts = key.split(".")
        instance = self

        for part in parts:
            instance = instance._get_1(part)

            if instance is None:
                return self._lift_raw_object(default)

        return instance

    def getp(self, key: str, default=None):
        self._assure_dict("getp")
        instance = self

        while instance is not None:
            value = instance.get(key)
            if value is not None:
                return value

            instance = instance.get_parent()

        return self._lift_raw_object(default)


class _TypedObjectTree(_ObjectTreeDictAdapter):
    def __init__(self, obj=None, parent=None):
        super().__init__(obj, parent)

    def get_type(self):
        obj = self.get_object()

        if not isinstance(obj, dict):
            return type(obj)

        if LIST_META_KEY not in obj:
            return dict

        self._verify_valid_list_with_metadata()
        return list

    def istype(self, clazz):
        return self.get_type() == clazz

    def is_native_type(self, clazz):
        return isinstance(self.get_object(), clazz)

    def astype(self, clazz):
        if isinstance(clazz, str):
            clazz = locate(clazz)

        if clazz == list:
            return self._aslist()

        obj = self.get_object()
        assert isinstance(
            obj, clazz
        ), f"Type mismatch: expected {clazz}, found {type(obj).__name__}"

        return obj

    def _aslist(self):
        obj = self.get_object()

        if isinstance(obj, list):
            return obj

        self._verify_valid_list_with_metadata()
        return obj[LIST_META_KEY].astype(list)

    def _verify_valid_list_with_metadata(self):
        obj = self.get_object()

        assert (
            isinstance(obj, dict)
            and LIST_META_KEY in obj
            and obj[LIST_META_KEY].istype(list)
        )


class Config(_TypedObjectTree, IgnoredPathsManager):
    def __init__(self, obj=None, parent=None):
        _TypedObjectTree.__init__(self, obj, parent)
        IgnoredPathsManager.__init__(self, obj=self)

    def to_dict(self):
        if self.is_native_type(dict):
            obj = {key: value.to_dict() for key, value in self.get_object().items()}

            # Only add ignored-paths to where they are actually defined
            # Otherwise, it makes a mess.
            key = IgnoredPathsManager.IGNORED_PATHS_META_KEY
            if key in self:
                obj[key] = self.get_ignored_paths().str_list

            return obj

        if self.is_native_type(list):
            return [item.to_dict() for item in self.get_object()]

        return self.get_object()
