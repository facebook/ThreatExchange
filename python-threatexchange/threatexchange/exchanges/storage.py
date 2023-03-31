import dbm
from abc import ABC, abstractmethod
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from typing import TypeVar 
import typing as t
import pickle

T = t.TypeVar('T')

class GenericStorage(ABC):

    @abstractmethod
    def connect(self, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def exists(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get(self, key: T):
        raise NotImplementedError

    @abstractmethod
    def set(self, key: T, val: T):
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, key: T):
        raise NotImplementedError
    
    @abstractmethod
    def drop(self, *args, **kwargs):
        raise NotImplementedError

class DBMStorage(GenericStorage):

    def __init__(self) -> None:
        self.db = None
        self.file = None
        self.next_key = None
    
    def connect(self, file: str):
        self.db = dbm.open(file, flag = 'c')
        self.file = file
        return self
    
    def exists(self) -> bool:
        return dbm.whichdb(self.file) is not None
    
    def drop(self):
        self.db.close() # close current connection
        # open database with 'n' flag to create new db and close
        # this should wipe out all keys and values for given collab db
        dbm.open(self.file, 'n').close()
    
    def get(self, key: T) -> t.Optional[str]:
        k = pickle.dumps(key)
        return pickle.loads(self.db[k]) if k in self.db else None
    
    def set(self, key: T, val: T):
        k, v = map(pickle.dumps, [key, val])
        self.db[k] = v

    def delete(self, key: T):
        del self.db[key]

    def __iter__(self):
        self.next_key = self.db.firstkey()
        return self
    
    def __next__(self):
        if (not self.next_key):
            raise StopIteration
        curr_key = self.next_key
        self.next_key = self.db.nextkey(curr_key)
        k, v = map(pickle.loads, [curr_key, self.db[curr_key]])
        return k, v

    def __del__(self):
        self.db.close()
