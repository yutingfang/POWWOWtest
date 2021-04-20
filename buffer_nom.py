# buffer structure: FIFO, circular
#   self.data [] : a list store data
#   self.store int: count data units stored in the buffer
#   self.head int: point to begin to data stream
#   self.tail int：point to end to data stream 
#   add(): add new data to tail of list
#          if overflow - drop tail of list, report lost, add new data to head
#          runtime: O(1)
#   remove(): return and drop head of list if buffer not empty
#             return None if buffer empty
#             runtime: O(1)

import collections
import multiprocessing as mp

class Buffer_plain:
     CONST_BUFFER_SIZE = 1000

     def __init__(self):
          super(Buffer_plain, self).__init__() #inherit from the object class
          #self.mgr = mp.Manager() #the mem manager allows for access from multiple processes
          self.data = list([None]*self.CONST_BUFFER_SIZE) #the shared mem list actually stores the data
          self.store = 0
          self.head = 0
          self.tail = -1
          self.lock = mp.Lock() # use locks to support shared access since list is not locked by default

          self.index =0


     def add(self, words):
          #with self.lock:
          # if full: overflow, drop tail of list, add new data to head
               if self.store == self.CONST_BUFFER_SIZE:
                    lost = self.data[self.head]
                    #print("WARNNING: buffer ",self.index.value, " overflow. Losing Data: %s" % lost)
                    self.data[self.head] = words
                    self.head = (self.head + 1) % self.CONST_BUFFER_SIZE
                    self.tail = (self.tail + 1) % self.CONST_BUFFER_SIZE
               # not full: add new data to tail
               else:
                    self.tail = (self.tail + 1) % self.CONST_BUFFER_SIZE
                    self.data[self.tail] = words
                    self.store += 1
                    if self.store == self.CONST_BUFFER_SIZE:
                         print("ALERT: buffer ",self.index, " is full.")

     def remove(self):
          # if empty: return None
          #with self.lock:
               if self.store == 0:
                    print("ALERT: buffer ",self.index, " is empty.")
                    return None
               # not empty: return head of list
               tmp = self.data[self.head]
               self.head = (self.head + 1) % self.CONST_BUFFER_SIZE
               self.store -= 1
               return tmp

     def ready(self):
          #with self.lock:
               return (self.store > 0)

     def full(self):
        # with self.lock:
             return (self.store ==self.CONST_BUFFER_SIZE)




     #
     # def __init__(self, mng):
     #      super(Buffer_plain, self).__init__() #inherit from the object class
     #      #self.mgr = mp.Manager() #the mem manager allows for access from multiple processes
     #      self.data = mng.list([None]*self.CONST_BUFFER_SIZE) #the shared mem list actually stores the data
     #      self.store = mng.Value('i',0)
     #      self.head = mng.Value('i',0)
     #      self.tail = mng.Value('i',-1)
     #      self.lock = mp.Lock() # use locks to support shared access since list is not locked by default
     #
     #      self.index = mng.Value('i',0)
     #
     # def add(self, words):
     #      with self.lock:
     #           # if full: overflow, drop tail of list, add new data to head
     #           if self.store.value == self.CONST_BUFFER_SIZE:
     #                lost = self.data[self.head.value]
     #                # print("WARNNING: buffer ",self.index.value, " overflow. Losing Data: %s" % lost)
     #                self.data[self.head.value] = words
     #                self.head.value = (self.head.value + 1) % self.CONST_BUFFER_SIZE
     #                self.tail.value = (self.tail.value + 1) % self.CONST_BUFFER_SIZE
     #           # not full: add new data to tail
     #           else:
     #                self.tail.value = (self.tail.value + 1) % self.CONST_BUFFER_SIZE
     #                self.data[self.tail.value] = words
     #                self.store.value += 1
     #                if self.store.value == self.CONST_BUFFER_SIZE:
     #                     print("ALERT: buffer ", self.index.value, " is full.")
     #
     # def remove(self):
     #      # if empty: return None
     #      with self.lock:
     #           if self.store.value == 0:
     #                print("ALERT: buffer ", self.index.value, " is empty.")
     #                return None
     #           # not empty: return head of list
     #           tmp = self.data[self.head.value]
     #           self.head.value = (self.head.value + 1) % self.CONST_BUFFER_SIZE
     #           self.store.value -= 1
     #           return tmp
     #
     # def ready(self):
     #      with self.lock:
     #           return (self.store.value > 0)
     #
     # def full(self):
     #      with self.lock:
     #           return (self.store.value == self.CONST_BUFFER_SIZE)
     #
     # def __str__(self):
     #      with self.lock:
     #           return str(self.data)
