class Model :
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', None)
        for k in self.__data__ :
            try :
                setattr(self, k, kwargs[k])
            except KeyError :
                try :
                    setattr(self, k, self.__default_data__[k])
                except KeyError :
                    raise TypeError("Expecting keyword argument '%s'" % k)
    def serialize(self) :
        return { k : getattr(self, k) for k in self.__data__ }
