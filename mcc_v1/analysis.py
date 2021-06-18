import sqlite3
import sys
import json

def read_unique_data(db_name):

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    output = [x[0] for x in cur.execute('SELECT DISTINCT TX FROM uniqueMAC1')]
    
    cur.close()
    conn.close()

    return output


if __name__ == '__main__':

    db_name = 'test.db'
    output_file = 'output.json'
    output_dir = sys.argv[1]

    db_path = output_dir+'/'+db_name
    output_path = output_dir+'/'+output_file

    result = read_unique_data(db_path)
    print("Unique MAC:")
    print(result)
    with open(output_path, 'w') as f:
        json.dump(result, f)