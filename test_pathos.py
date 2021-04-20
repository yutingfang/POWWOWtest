from pathos.multiprocessing import ProcessingPool
from multiprocessing import Manager, Process
from multiprocessing.managers import BaseManager


class Bar:
    sum = 0

    def foo(self, name):
        return len(str(name))

    def boo(self, things):
        for thing in things:
            self.sum += self.foo(thing)
        return self.sum

class Buffer:
    def __init__(self):
    #     #self.mng =
    #     #self.data = mng.list()
        self.data = []
    def add(self, value):
        self.data.append(value)
        print("add value:", value)
        print("buffer:", self.data)
    def remove(self):
        return self.data

class BufferManager(BaseManager):
    pass

BufferManager.register('Buffer', Buffer)

def add_buffer(buffer):
    buffer.add(1)

if __name__ == '__main__':

    mng = BufferManager()
    mng.start()
    b = mng.Buffer()

    p = Process(target = add_buffer, args=(b,))
    p.start()
    #results = ProcessingPool().map(add_buffer, [b[0], b[1]])
    p.join()

    print("check value:", b.remove())
