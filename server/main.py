import webbrowser
from tkinter import ttk
from tkinter import *
import logging
from flask import Flask, request, jsonify, render_template, templating
from flask_cors import CORS
import json
import serial
import threading
import os
import serial.tools.list_ports
import time

ser = serial.Serial()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

print('\nСервер настройки индивидуального устройства системы "Умная дача СКБ-4"\n')

window = Tk()
window.title("Умная дача СКБ-4")
window.geometry('400x250')
imgicon = PhotoImage(file=os.path.join(os.path.realpath('icon.png')))
#imgicon = PhotoImage("")
window.tk.call('wm', 'iconphoto', window._w, imgicon)

new = 1
url = "http://localhost:5000"

def openweb():
    webbrowser.open(url, new=new)

Btn = Button(window, text="Открыть веб-интерфейс", command=openweb)
Btn.pack()

app = Flask(__name__, static_url_path='')
CORS(app)

cors = CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})

Com_port_json = {
    "com_devices": [],

    "com_speed": [
        50,
        75,
        110,
        150,
        300,
        600,
        1200,
        2400,
        4800,
        9600,
        19200,
        38400,
        57600,
        115200
    ]
}
# looking for devices


def checkComDevices():
    Com_port_json["com_devices"] = []
    ports = serial.tools.list_ports.comports()
    n = 0
    for port, desc, hwid in sorted(ports):
        Com_port_json["com_devices"].append(
            {"id": n, "port": port, "name": port + "/" + desc})
        n += 1


connect_data = {"port": 0, "speed": 0}

check = {}

deviceConnected = False

terminal = {"chat": []}


@app.route("/check", methods=["GET"])
def checkworking():
    check["server_working"] = "true"
    check["device_port"] = connect_data["port"]
    global deviceConnected

    '''if ser.is_open:
        print("device connected")
    else:
        print("no connection")'''

    try:
        ser.write(b' ')
        ser.read(1)
        deviceConnected = True
        #print("connection ok")
    except:
        #print("cannot write")
        deviceConnected = False
        ser.close()

    check["device_connected"] = "true" if deviceConnected == True else "false"

    return jsonify(check)


'''@app.route("/com/connect", methods = ["GET", "POST"])
def connect():
    
    print("lol")
    if request.method == 'POST':
        
        value = request.json
        print(value)
            
        return jsonify(value)'''


def readline(port):
    message = ""
    byte = ""
    while True:
        byte = port.read()
        if byte == "\n":
            break
        message += str(byte)
    return message


@app.route("/", methods=["GET", "POST"])
def json_test():
    return render_template("index.html")


@app.route("/com/show", methods=["GET", "POST"])
def func():
    checkComDevices()
    # print(Com_port_json)
    return jsonify(Com_port_json)


@app.route("/com/connect", methods=["GET", "POST"])
def connect_data_func():
    value = request.json
    global deviceConnected

    if request.method == 'POST':
        value = request.json
        connect_data["reply"] = "success"

        parse_data = json.loads(json.dumps(value))
        if "port" in parse_data:
            connect_data["port"] = parse_data["port"]
        if "speed" in parse_data:
            connect_data["speed"] = parse_data["speed"]

    try:
        ser.baudrate = connect_data["speed"]
        ser.port = connect_data["port"]
        ser.timeout = 1
        ser.open()
        time.sleep(1)
        #print('-- Successfully connected')
        deviceConnected = True
    except Exception:
        #print('-- Error: Could not connect')
        deviceConnected = False

    return jsonify(connect_data)


@app.route("/com/disconnect", methods=["POST"])
def comDisconnect():
    value = request.json
    global terminal
    terminal = {"chat": []}

    if request.method == 'POST':
        value = request.json

        parse_data = json.loads(json.dumps(value))
        if parse_data["command"] == "disconnect":
            ser.close()
            #print("closed")
            return jsonify({"reply": "success"})
        else:
            return jsonify({"reply": "error"})


@app.route("/com/send", methods=["GET", "POST"])
def sendCommand():
    value = request.json

    if request.method == 'POST':
        value = request.json

        parse_data = json.loads(json.dumps(value))
        if "command" in parse_data:
            terminal["chat"].append(
                {"message": value["command"], "author": "user"})

    try:
        for i in range(1, len(value["command"]) + 1):
            ser.write(value["command"][i-1].encode())
        #print('-- send')
    except Exception:
        #print('-- error')
        pass

    # ser.flush()
    import time
    time.sleep(.1)
    s = ser.readline()
    terminal["chat"].append(
        {"message": str(s.decode("utf-8")), "author": "device"})
    #print(s)

    return jsonify(terminal)


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "500"})


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404"})


@app.errorhandler(400)
def not_found(error):
    return jsonify({"error": "400"})


def flask_start():
    app.run('0.0.0.0', port='5000')


def tkinter_start():
    window.mainloop()


if __name__ == "__main__":
    flt = threading.Thread(target=flask_start)
    flt.daemon = True
    flt.start()
    tkinter_start()
