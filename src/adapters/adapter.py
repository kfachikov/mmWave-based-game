import abc

from Tracking import TrackBuffer

class Adapter(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'update') and 
                callable(subclass.update) or 
                NotImplemented)
    
    @abc.abstractmethod
    def update(self, trackbuffer: TrackBuffer, **kwargs):
        """
        Update the visualizer with the current data.
        """
        raise NotImplementedError