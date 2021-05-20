import sqlite3

# db_name = the name of the database
def create_table_db(db_name):
    # SQL statements
    sql_drop_entries = '''
        DELETE FROM uniqueMAC1;
    '''
    sql_create_table = '''
        CREATE TABLE IF NOT EXISTS uniqueMAC1(
            TX TEXT,
            RX TEXT,
            SNR REAL);
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
    print("--- Create Table Successfully ---")



def write_file_db(filename, db_name):

    # open a connection with the DB
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    with open(filename,'r') as f:
        for line in f:
            line = line.rstrip()   # strip white space
            words = line.split()   # split string into a list of words
            if len(words) == 3:    # only take lines with desired information
                cur.execute('INSERT INTO uniqueMAC1 (TX, RX, SNR) VALUES (?, ?, ?)', words)
                conn.commit() #we need to commit here or else the read values will not be seen by a parallel connection

    # commit and close db connection
    conn.commit()
    cur.close()
    conn.close()

    print("--- Done Writing Data to DB---")



if __name__ == '__main__':

    filename = "filedata.txt"
    db_name = 'test.db'

    create_table_db(db_name)
    write_file_db(filename, db_name)
    # result = read_unique_data(db_name)
    # print(result)


