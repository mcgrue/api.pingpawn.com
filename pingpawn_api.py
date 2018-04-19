from flask import Flask, request, jsonify, Blueprint, Response, abort

import MySQLdb
import MySQLdb.cursors as cursors

dbvars = {}
with open(".dbstuff") as myfile:
  for line in myfile:
    name, var = line.partition("=")[::2]
    dbvars[name.strip()] = var.strip()


def do(query, args=False):
  connection = MySQLdb.connect(
    host=dbvars['host'], user=dbvars['user'],
    passwd=dbvars['passwd'], db=dbvars['db'],
    cursorclass=cursors.DictCursor
  )

  result = None

  try:
    with connection as cursor:
      if not args:
        cursor.execute(query)
      else:
        cursor.execute(query, args)
    
    res = cursor.fetchone()

    print(res)

    if res is None:
      res = {"Error": "No result :("}

    result = jsonify(res)

    connection.close()
  except:
    print("QUERY:\n==========\n")
    print(query)

    print("ARGS:\n==========\n")
    print(args)

  return result

bp = Blueprint('bp', __name__)

@bp.route('/')
def index():
  return do("SELECT * FROM quotes ORDER BY RAND() LIMIT 1")
  

@bp.route('/rand', defaults={'prf': False}, strict_slashes = False)
@bp.route('/rand/<prf>', strict_slashes = False)
def rand(prf=None):
  """
  http://api.pingpawn.com/rand – Get a random quote
  http://api.pingpawn.com/rand/grue – Get a random quote from a specific quotefile
  """

  size_limit = request.args.get('size_limit', False)

  if size_limit:
    size_limit =  ' AND LENGTH(q.quote) <= ' + str(int(size_limit)) + ' ' 
  else:
    size_limit = ' AND 1=1 '

  if not prf:
    return do("SELECT * FROM `quotes` q WHERE q.is_public = 1 "+size_limit+" ORDER BY RAND() LIMIT 1")
  else:
    return do("SELECT q.* FROM `quotes` q, `prfs` p WHERE p.name = %s "+size_limit+" AND p.id = q.prf_id AND q.is_public = 1 ORDER BY RAND() LIMIT 1", [prf])


@bp.route('/search/', defaults={'prf': False, 'offset': False}, strict_slashes = False)
@bp.route('/search/<prf>', defaults={'offset': False}, strict_slashes = False)
@bp.route('/search/<prf>/<offset>', strict_slashes = False)
def search(prf, offset):
  """
  http://api.pingpawn.com/search?q=ATTEMPT+to+not+be+a+chump – Search for quotes that match a certain phrase (a random quote from the set of all that match).
  http://api.pingpawn.com/search/grue?q=fire – Search for quotes that match a certain phrase from a certain quotefile (a random quote from the set of all that match)
  http://api.pingpawn.com/search/grue/2?q=fire – Search for quotes that match a certain phrase from a certain quotefile, deterministically (this is the second quote in this quotefile that matches, and always will be.)
  """

  size_limit = request.args.get('size_limit', False)
  q = request.args.get('q', '')
  
  if size_limit:
    size_limit =  ' AND LENGTH(q.quote) <= ' + str(int(size_limit)) 
  else:
    size_limit = ""

  if not offset:
    offset = " ORDER BY RAND() "
  else:
    offset = " LIMIT %s,1" % (int(offset)-1)
  
  if q:  
    q = q.replace('*', '%') 
    q = '%' + q + '%'
    print(q)

  if prf == '~~~NOBODY~~~':
    prf = False

  if not prf:
    sql = "SELECT q.* FROM `quotes` q WHERE q.is_public = 1 "+size_limit+" AND q.quote LIKE %s "
    args = [q]
  else:
    if q:
      sql = "SELECT q.* FROM `quotes` q, `prfs` p WHERE p.name = %s "+size_limit+" AND q.quote LIKE %s AND p.id = q.prf_id AND q.is_public = 1 " 
      args = [prf, q]
    else:
      sql = "SELECT q.* FROM `quotes` q, `prfs` p WHERE p.name = %s "+size_limit+" AND p.    id = q.prf_id AND q.is_public = 1 " 
      args = [prf]

  sql = sql + offset

  print(sql)

  return do(sql, args) 


@bp.route('/count/', defaults={'prf': False}, strict_slashes = False)
@bp.route('/count/<prf>', strict_slashes = False)
def count(prf):
  """
  http://api.pingpawn.com/count/gayo/?q=taco
  http://api.pingpawn.com/count/grue/?q=taco
  http://api.pingpawn.com/count/?q=taco
  """

  size_limit = request.args.get('size_limit', False)
  q = request.args.get('q', '')
  
  if size_limit:
    size_limit =  ' AND LENGTH(q.quote) <= ' + str(int(size_limit)) 
  else:
    size_limit = ""

  if q:  
    q = q.replace('*', '%') 
    q = '%' + q + '%'
    print(q)
  if not q:
    abort(400)

  if not prf:
    sql = "SELECT count(*) as my_count FROM `quotes` q WHERE q.is_public = 1 "+size_limit+" AND q.quote LIKE %s "
    args = [q]
  else:
    sql = "SELECT count(*) as my_count FROM `quotes` q, `prfs` p WHERE p.name = %s "+size_limit+" AND q.quote LIKE %s AND p.id = q.prf_id AND q.is_public = 1 " 
    args = [prf, q]

  return do(sql, args) 

app = Flask(__name__)
app.register_blueprint(bp)
app.url_map.strict_slashes = False

