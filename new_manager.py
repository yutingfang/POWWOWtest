# Test： multiple buffers + Process(target, args)
# splite orginal file into smaller files  
# each process read one file into one buffer

import os
import sys
import time
import math
import multiprocessing
from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue, Pool, Manager
from buffer import Buffer
from buffer_nom import Buffer_plain
from helper import file_iterations, split_file, visualize
import dill

class BufferManager(BaseManager):
    pass

BufferManager.register('Buffer', Buffer_plain)


# function processe to call
def stream_sender(filename, buffer, count):

    sent_ct = 0 
    with open(filename,'r') as f:
        for line in f:
            line = line.rstrip()   # strip white space
            words = line.split()   # split string into a list of words
            if len(words) == 3:    # only take lines with desired information
                    buffer.add(words)
                    sent_ct += sys.getsizeof(words)   # take bit size of records
    count.put(sent_ct)
     
# driver function to test different num of workers
def test_mfmb(num_workers):

    print("--- Running Test with workers:", num_workers)
    file = 'filedata.txt'
    newfile = 'split_file'
    
    # create buffers array, one for each process
    # each buffer managed by the shared memory manager
    buffers = []
    files = []

    ##############
    mng = BufferManager()
    mng.start()

    for i in range(num_workers):
        #buffers.append(Buffer_plain(Manager()))
        buffers.append(mng.Buffer())
        # buffers[i].index = i
        files.append('%s%d.txt' % (newfile, i))
    
    # create splited files
    split_file(num_workers, file, newfile)

    # pool for collecting process
    # sent_ct - use shared memory Queue to store # of records processed
    pool = []
    sent_ct = Queue()

    ##### invoke proccesses
    startTime = time.time()
    for i in range(num_workers):
        p = Process(target = stream_sender, args = (files[i], buffers[i], sent_ct))
        p.start()
        pool.append(p)

    for p in pool:
        p.join()

    t = time.time() - startTime
    
    # check number of records in each buffer
    for i in range(len(buffers)):
        print("Buffer ", i+1, " records #: ", buffers[i].remove())
        os.remove(files[i])

    # calculate total size of data streamed into buffer
    total = 0
    while not sent_ct.empty():
        total += sent_ct.get()
    
    return t, total


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())


if __name__ == '__main__':

    # make larger file
    file_iterations('filedata.txt', 100000, 'newfile.txt')

    print("CPU:", multiprocessing.cpu_count())
    # # of processes
    n = [1, 2, 3, 4, 5]
    # times of processing, and total size of data streamed into buffer
    times = []
    sizes = []

    for i in n:
        result = test_mfmb(i)
        times.append(result[0])
        sizes.append(result[1])
    
    visualize(times, n, sizes)