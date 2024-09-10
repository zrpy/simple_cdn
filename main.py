import flask,os,time,random,string,math,psutil,hashlib
os.system("mkdir uploads")
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps

app=flask.Flask("Cdn Server")
app.config['UPLOAD_FOLDER'] = './uploads'
host="http://localhost:8080"
access_count=0


def randomstring(n):
   randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
   return ''.join(randlst)


def get_dir_size(path='.'):
    total_size = 0
    for f in os.listdir(path):
            if os.path.isfile(os.path.join(path,f)):
                total_size+=os.path.getsize(os.path.join(path,f))
            elif os.path.isdir(os.path.join(path,f)):
                total_size+=get_dir_size(os.path.join(path,f))
    return total_size


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def access_counter(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global access_count
        access_count += 1
        return await func(*args, **kwargs)
    return wrapper


@app.route('/uploads', methods=['POST'])
@access_counter
async def upload_files():
    if len(flask.request.files)==0:
        return flask.jsonify({"error":"file is not uploaded"})
    files = flask.request.files.getlist('files')
    file_list = []
    for file in files:
        if file.filename == '':
            continue
        file_name = secure_filename(file.filename)
        file_hash=hashlib.sha256((os.path.splitext(file_name)[0]+"."+str(int(time.time()))+"."+str(random.randint(0,999))).encode()).hexdigest()
        after_file_name = file_hash+os.path.splitext(file_name)[1]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], after_file_name))
        file_list.append({"file_name":after_file_name,"file_hash":file_hash,"file_upload":int(time.time()),"url":host+"/uploads/"+after_file_name})
    return flask.jsonify([i for i in file_list])

@app.route('/uploads/<file_id>')
@access_counter
async def uploaded_file(file_id):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_id)


@app.route("/",methods=["GET"])
@access_counter
async def index():
    return flask.jsonify({"author":"zrpy"})


@app.route("/usage")
@access_counter
async def usage():
    dir=os.getcwd()+"/uploads"
    memory = psutil.virtual_memory().percent
    return flask.jsonify({"file_size":convert_size(get_dir_size(dir)),"file_count":"","memory_percentage":memory,"access_count":access_count})


app.run(host="0.0.0.0",port=8080)
