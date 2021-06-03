import sqlite3

def read_unique_data(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute('SELECT TX FROM (SELECT * FROM uniqueMAC1) GROUP BY TX')
    #print('Printing analysis data')
    output=[]
    for row in cur:
        output.append(row)
    
    conn.commit()
    cur.close()
    conn.close()

    return output


if __name__ == '__main__':

    filename = "filedata.txt"
    db_name = 'test.db'

    # create_table_db(db_name)
    # write_file_db(filename, db_name)
    result = read_unique_data(db_name)
    print("Unique MAC:")
    print(result)


