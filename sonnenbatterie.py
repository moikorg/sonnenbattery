import requests
import sqlite3

def getSonnenData():
    r = requests.get('http://SB-41059:8080/api/v1/status')
    return r.json()

def main():
    conn = sqlite3.connect('sonnen.sql')
    c = conn.cursor()

    # create table
    sql = """
     CREATE TABLE battery
     (consumption INTEGER, frequency INTEGER, gridConsumption INTEGER, isSystemInstalled INTEGER, pacTotal INTEGER,
     production INTEGER, rsoc INTEGER, timestamp TEXT, ts INTEGER PRIMARY KEY DESC, usoc INTEGER, uAC INTEGER, uBat INTEGER)
     """
    c.execute(sql)

    # create additional index
    sql = """
        CREATE INDEX index_timestamp ON battery (timestamp ASC)
    """
    c.execute(sql)

    conn.commit()
    conn.close()

    exit(1)



    sonnenData = getSonnenData()
    print(sonnenData)

# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()