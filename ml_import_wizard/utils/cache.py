from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from collections import OrderedDict


class LRUCacheThing():
    """" Cache things with Least Recently Used.  Has stupid name to avoid colisions """

    def __init__(self, *, items: int=100):
        """ Initialize with 100 items by default """

        self.things: OrderedDict = OrderedDict()
        self.transaction_things: OrderedDict = OrderedDict()
        self.items: int = items
    
    def store(self, *, key: any, value: any, transaction: bool = False) -> any:
        """ Store a key/value in the cache.  
        If transaction, temporarilly stores in transaction_things so they can be thrown out with rollback or committed with commit """
        
        if transaction:
            self.transaction_things[key] = value
            self.transaction_things.move_to_end(key)

        else:
            self.things[key] = value
            self.things.move_to_end(key)

            if len(self.things) > self.items:
                self.things.popitem(last=False)

    def find(self, *, key: any, report: bool=False, output: str="print") -> any:
        """ Return the object found using the key, or none """

        if key in self.transaction_things:
            self.transaction_things.move_to_end(key)
            if report: 
                if output == "print":
                    print(f"Found key in transaction: {key}")
                else:
                    log.debug(f"Found key in transaction: {key}")

            return self.transaction_things[key]

        if key in self.things:
            self.things.move_to_end(key)
            if report: 
                if output == "print":
                    print(f"Found key: {key}")
                else:
                    log.debug(f"Found key: {key}")

            return self.things[key]
        
        if report: 
            if output == "print":
                print(f"Didn't find key: {key}")
            else:
                log.debug(f"Didn't find key: {key}")

        return None
    
    def rollback(self) -> None:
        """ Roll back by removing all things in transaction_things """

        self.transaction_things.clear()

    def commit(self) -> None:
        """ Add all items in transaction_things to things """

        for key, value in self.transaction_things.items():
            self.store(key=key, value=value)

        self.transaction_things.clear()

    @property
    def count(self) -> int:
        """ Get the count of things in the cache """
        
        return len(self.things)

    @property 
    def transaction_count(self) -> int:
        """ Get the count of transaction_things in the cache """

        return len(self.transaction_things)
    
    def __len__(self) -> int:
        """ Return the count of transaction_things + things """

        return len(self.things) + len(self.transaction_things)