import abc


class Object(abc.ABC):
    def build(self):
        pass

    @abc.abstractmethod
    def difference(self):
        pass

    @abc.abstractmethod
    def backup(self):
        pass

    @abc.abstractmethod
    def apply(self):
        pass
