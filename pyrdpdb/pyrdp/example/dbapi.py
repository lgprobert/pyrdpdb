import sys

from pyrdpdb import pyrdp


def simple(host: str):
    print("\nBasic query with cursor:\n")
    conn = pyrdp.connect(host=host, port=4333, user="RAPIDS", password="rapids")
    sql = "select * from region"
    cur = conn.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    print(res)


def sscursor(host: str):
    print("\nUsing SSCursor:\n")
    conn = pyrdp.connect(
        host=host,
        port=4333,
        user="RAPIDS",
        password="rapids",
        cursorclass=pyrdp.SSCursor,
    )
    with conn.cursor() as cursor:
        cursor.execute("select * from nation limit 5")
        for r in cursor:
            print(r)


def main(host: str):
    simple(host)
    sscursor(host)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    main(host)
