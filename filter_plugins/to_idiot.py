#!/usr/bin/python3

class FilterModule(object):
    def filters(self):
        return {
            'to_idiot': self.to_idiot,
        }

    def to_idiot(self, value):
        return_string = ""
        for i in range(0, len(value)):
            if i % 2 == 0:
                return_string += str(value[i]).lower()
            else:
                return_string += str(value[i]).upper()
        return return_string