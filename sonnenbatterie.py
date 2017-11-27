import requests
import sqlite3

def getSonnenData():
    r = requests.get('http://SB-41059:8080/api/v1/status')
    return r.json()

def main():
    conn = sqlite3.connect('sonnen.sql')
    c = conn.cursor()

    sql = """
      CREATE TABLE battery
     (consumption INTEGER, frequency INTEGER, gridConsumption INTEGER, isSystemInstalled INTEGER, pacTotal INTEGER,
     production INTEGER, rsoc INTEGER, ts TEXT , usoc INTEGER, uAC INTEGER, uBat INTEGER)
     """
    # create table
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