import os
import sys
import time
import math
import multiprocessing
import multiprocessing as mp
import sqlite3
from multiprocessing import Process, Queue, Pool, Manager

# from buffer import Buffer
# from sync_manager import SyncManager
# from db_utils import create_table_db,log_results,read_all_records_db,analysis
# from workers import stream_sender, stream_receiver, realtime_analysis
# from helper import file_iterations, split_file, visualize

class Buffer:
     CONST_BUFFER_SIZE = 1000

     def __init__(self):
          super(Buffer, self).__init__() #inherit from the object class
          self.mgr = mp.Manager() #the mem manager allows for access from multiple processes
          self.data = self.mgr.list([None]*self.CONST_BUFFER_SIZE) #the shared mem list actually stores the data
          self.store = self.mgr.Value('i',0)
          self.head = self.mgr.Value('i',0)
          self.tail = self.mgr.Value('i',-1)
          self.lock = mp.Lock() # use locks to support shared access since list is not locked by default

          self.index = self.mgr.Value('i',0)

    
     def add(self, words):
          with self.lock:
          # if full: overflow, drop tail of list, add new data to head
               if self.store.value == self.CONST_BUFFER_SIZE:
                    lost = self.data[self.head.value]
                    #print("WARNNING: buffer ",self.index.value, " overflow. Losing Data: %s" % lost)
                    self.data[self.head.value] = words
                    self.head.value = (self.head.value + 1) % self.CONST_BUFFER_SIZE
                    self.tail.value = (self.tail.value + 1) % self.CONST_BUFFER_SIZE
               # not full: add new data to tail
               else:
                    self.tail.value = (self.tail.value + 1) % self.CONST_BUFFER_SIZE
                    self.data[self.tail.value] = words
                    self.store.value += 1
                    if self.store.value == self.CONST_BUFFER_SIZE:
                         print("ALERT: buffer ",self.index.value, " is full.")

     def remove(self):
          # if empty: return None
          with self.lock:
               if self.store.value == 0:
                    print("ALERT: buffer ",self.index.value, " is empty.")
                    return None
               # not empty: return head of list  
               tmp = self.data[self.head.value]
               self.head.value = (self.head.value + 1) % self.CONST_BUFFER_SIZE
               self.store.value -= 1
               return tmp

     def ready(self):
          with self.lock:
               return (self.store.value > 0)
    
     def full(self):
         with self.lock:
             return (self.store.value ==self.CONST_BUFFER_SIZE)

     def __str__(self):
          with self.lock:
               return str(self.data)

class SyncManager:
    
     def __init__(self):
          super(SyncManager, self).__init__() #inherit from the object class
          self.mgr = mp.Manager() #the mem manager allows for access from multiple processes
          self.count = self.mgr.Value('i',0)
          self.last_id = self.mgr.Value('i',0)
          self.lock = mp.Lock() # use locks to support shared access since list is not locked by default
     
     # called by the stream processor when it is done streaming
     def stop(self,last_id): 
          with self.lock:
               self.count.value = 1
               self.count.last_id = last_id

     # called by the db analytics when it wants to know the last search value. 
     def get_last_id(self):
         return self.last_id 

     # returns true if the signal is still streaming
     def sending(self):
          return (self.count.value == 0)

def create_table_db(db_name):
    # SQL statements
    sql_drop_entries = '''
        DELETE FROM uniqueMAC1;
    '''
    sql_create_table = '''
        CREATE TABLE IF NOT EXISTS uniqueMAC1(
            TX TEXT,
            RX TEXT,
            SNR REAL,
            ID REAL);
        '''
    # connect to database
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    # execute sql
    cur.execute(sql_create_table)
    cur.execute(sql_drop_entries)

    # end up execution
    con.commit()
    cur.close()
    con.close()

def read_all_records_db(db_name):
    # SQL statements
    sql_read_record = '''
        SELECT * FROM uniqueMAC1;
        '''
    # connect to database
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    # execute sql
    cur.execute(sql_read_record)
    result = cur.fetchall()
    # end up execution
    con.commit()
    cur.close()
    con.close()
    return result

def log_results(results):
    with open('query_output','w') as f:
        for r in results:
            tx = r[0]
            rx = r[1]
            snr = r[2]
            id=r[3]
            f.write('{},{},{},{}'.format(tx,rx,snr,id))

def printlog(db_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    cur.execute('SELECT * FROM uniqueMAC1')
    for row in cur:
        print(row)

def stream_sender(filename, buffer, count):
    #info('sender')
    sent_ct = 0 
    with open(filename,'r') as f:
        for line in f:
            line = line.rstrip()   # strip white space
            words = line.split()   # split string into a list of words
            if len(words) == 3:    # only take lines with desired information
                    buffer.add(words)
                    sent_ct += sys.getsizeof(words)   # take bit size of records
    count.put(sent_ct)

    # acknowledge to the log that stream_receiver has stopped 
    # sending new inputs to the buffer
    print('ALERT: stream_sender stopped sending packets')
    print('STATS: sent tuples: {}'.format(sent_ct))


# given a shared buffer, stream_receiver reads the 
# buffer and inserts the buffer items into the database
# the process stops after 5 seconds of no new insertions
# into the empty buffer
#    buffer = a instance of the Buffer class to read
#    wait = the time in seconds to wait before reading again
#         after reading an empty buffer 
#    max_time = the max number of seconds to wait for a new buffer 
#         entry before terminating the process
#    buffers - buffer array rotate on
def stream_receiver(buffers,sm,wait,max_time):
        #info('receiver')

        # open a connection with the DB
        conn = sqlite3.connect('test.db')
        cur = conn.cursor()

        # keep track of the # of consecutive times the buffer was empty 
        # when attempting to be read
        empty_ct = 0 

        # keep track of the number of packets read out of the buffer
        read_ct = 0
        print('streaming start: {}'.format(time.time()))

        while empty_ct < max_time: 
            for buffer in buffers:  # rotate on buffers
                # attempt to read from the buffer
                if buffer.ready():
                    #print('reader buff state: {}'.format(buffer))
                    buff_item = buffer.remove()
                    buff_item.append(read_ct) #append an ID to the buffer item
                    cur.execute('INSERT INTO uniqueMAC1 (TX, RX, SNR, ID) VALUES (?, ?, ?, ?)',buff_item)
                    conn.commit() #we need to commit here or else the read values will not be seen by a parallel connection
                    empty_ct = 0 #reset the empty ct
                    read_ct += 1 
                else: 
                    #print('nothing to read')
                    time.sleep(wait)
                    empty_ct += 1 

        # notify the analysis function that the stream has ended
        sm.stop(read_ct)

        # TODO - is this the best setup for when to commit? 
        conn.commit()
        cur.close()
        conn.close()

        # acknowledge to the log that stream_receiver has stopped 
        # receiving new inputs to the buffer
        print('ALERT: steam_reciever stopped receiving packets')
        print('STATS: buffer empty: {} | read tuples: {}'.format(not buffer.ready(),read_ct))
        print('streaming end: {}'.format(time.time()))

# the realtime analysis runs a user-defined query / analsis on the data 
# after it has been entered into the database
def realtime_analysis(db_name, sm):

     print('analysis start: {}'.format(time.time()))
     f = open("analysis_results.txt", "w")

     # continue querying until stream stops
     while sm.sending(): 
          analysis(f)
          time.sleep(1) #try to read new data every 5 seconds

     f.close()
     print('analysis end: {}'.format(time.time()))

# log = a file pointer to log the output
def analysis(log):
   
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()

    cur.execute('SELECT TX FROM (SELECT * FROM uniqueMAC1 ORDER BY ID DESC LIMIT 10 ) GROUP BY TX')
    #print('Printing analysis data')
    output=[]
    for row in cur:
        output.append(row)

    cur.execute('SELECT RX FROM (SELECT * FROM uniqueMAC1 ORDER BY ID DESC LIMIT 10 ) GROUP BY RX ')
    for row in cur:
        output.append(row)

    conn.commit()
    conn.close()
    unique_output=set(output)
    log.write('{}\n'.format(len(unique_output)))

def file_iterations(filename, output_size, out_file):
    f = os.stat(filename)
    loops = math.floor(output_size/f.st_size)
    print("Need iteration: ", loops)

    with open(out_file, 'w') as outfile:
        for x in range(0, loops):
            with open(filename) as infile:
                outfile.write(infile.read())
    print("Large file produced.")

# helper function to split file
def split_file(num_workers, infile, outfile):
    with open(infile) as input:
        files = [open('%s%d.txt' % (outfile,i), 'w') for i in range(num_workers)]
        for i, line in enumerate(input):
            files[i % num_workers].write(line)
        for f in files:
            f.close()

# visualize data rate
def visualize(times, num_p, Bytes):
    times = numpy.array(times)
    Bytes = numpy.array(Bytes)
    rate = numpy.divide(Bytes, times)
    plt.plot(num_p, rate)
    plt.ylabel("KBps")
    plt.xlabel("Number of Processes")
    plt.savefig('data_rate.png')


def interagtion_test(num_senders):
    
    print("---- Number of senders:", num_senders)

    # setup the test variables
    origin_file = 'filedata.txt'
    genera_file = 'newfile.txt'
    splited_files = 'split_file'
    output_size = 100000
    wait_time = 1
    max_time = 5
    db_name = 'test.db'

    # make larger file and split file
    file_iterations(origin_file, output_size, genera_file)
    files = []                                              # create a array of splited file names to hold splited files
    for i in range(num_senders):
        files.append('%s%d.txt' % (splited_files, i))
    split_file(num_senders, genera_file, splited_files)     # split large file into # of files = num_sender
    
    # create buffers array, one buffer for each process
    # each buffer managed by the shared memory manager
    buffers = []
    for i in range(num_senders):
        buffers.append(Buffer())
        buffers[i].index.value = i

    #create a sync manager to share info between the receiver and the analytics
    sm = SyncManager()

    #setup the database
    create_table_db(db_name)

    #### invoke multiple senders
    
    sender_pool = []    # pool for collecting sender process
    sent_ct = Queue()   # sent_ct - use shared memory Queue to store # of records processed

    start = time.time() # start latency measurement

    for i in range(num_senders): 
        p = Process(target = stream_sender, args = (files[i], buffers[i], sent_ct)) # senders
        p.start()
        sender_pool.append(p)

    reader = Process(target=stream_receiver, args=(buffers,sm,wait_time,max_time))  # receivers
    analytics = Process(target=realtime_analysis, args=(db_name,sm))
    reader.start()
    analytics.start()

    for p in sender_pool:
        p.join()
    reader.join()
    analytics.join()

    t = time.time() - start # end latency measurement

    # attempt to read the database for the intial entries (this will eventually be PART 2)
    log_results(read_all_records_db(db_name))

    # end & clean up
    for i in range(num_senders):
        os.remove(files[i])

    total_bytes = 0                     
    while not sent_ct.empty():
        total_bytes += sent_ct.get()    # total memory size of data streamed into buffer
    total_Bytes = total_bytes/1000
    
    return t, total_Bytes

if __name__ == '__main__':

    num_senders = [1, 2, 3]
    times = []
    for n in num_senders:
        result = interagtion_test(n)
        print("time: ", result[0])
        print("data processed (Bytes): ", result[1])

    print("\nTimes: ", times)