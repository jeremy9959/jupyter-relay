import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
import subprocess
import shlex
import requests
from requests.exceptions import ConnectionError


# full path to  file to be served
watch_file_path = Path(sys.argv[1]).absolute()

# port on local machine where file is served
port = 5000

# name of html file (must match flask code in simple_flask.py)
html_file = "/tmp/relay.html"


# command to convert jupyter notebook to html
nbconvert_cmd = "jupyter nbconvert {} --to html --stdout".format(str(watch_file_path))

# command to start the web server
start_server_cmd = "gunicorn --bind 127.0.0.1:{} simple_flask:app".format(port)


def start_services():

    # start the ngrok relay
    try:
        _ = requests.get("http://localhost:4040/api")
    except ConnectionError:
        print(
            "ngrok is not available, please run\n~/ngrok start --none\nand then restart this script"
        )
        exit(1)

    ngrok_tunnel = {"name": "relay_tunnel", "addr": port, "proto": "http"}
    setup_tunnel = requests.post("http://localhost:4040/api/tunnels", json=ngrok_tunnel)
    tunnel = setup_tunnel.json()
    try:
        print("Relay will be available at:\n {}".format(tunnel["public_url"]))
    except KeyError:
        print("Failed to open ngrok tunnel, exiting")
        exit(1)

    # make sure there is a file to serve
    nbconvert = relay_html()

    # start the webserver
    try:
        web_server = subprocess.Popen(shlex.split(start_server_cmd))
    except OSError as e:
        print("Could not start webserver: {0} -- exiting".format(e))
        exit(1)
    return web_server, nbconvert


def relay_html():

    with Path(html_file).open("w") as f:
        print("writing to {}".format(html_file))
        try:
            nbconvert_process = subprocess.run(shlex.split(nbconvert_cmd), stdout=subprocess.PIPE,universal_newlines=True,check=True,stderr=subprocess.DEVNULL)
        except OSError as err:
            print("Error {0}:problem starting nbconvert process, aborting".format(err))
            exit(1)
        except subprocess.CalledProcessError as e:
            print("nbconvert command failed: {}".format(' '.join(e.cmd)))
            exit(1)
        f.write(nbconvert_process.stdout)
    return nbconvert_process


def make_new_html_file(event):
    relay_html()
    return


def do_nothing(event):
    return


def start_watchdog():
    pattern = [str(watch_file_path)]
    my_event_handler = PatternMatchingEventHandler(patterns=pattern)
    my_event_handler.on_created = make_new_html_file
    my_event_handler.on_deleted = do_nothing
    my_event_handler.on_modified = make_new_html_file
    my_event_handler.on_moved = make_new_html_file

    observer = Observer()
    observer.schedule(my_event_handler, str(watch_file_path.parents[0]), recursive=True)
    observer.start()
    return observer


def shutdown(web_server, observer):
    try:
        web_server.terminate()
    except subprocess.SubprocessError:
        print("web server did not  stop cleanly")

    observer.stop()
    try:
        _ = requests.delete("http://localhost:4040/api/tunnels/relay_tunnel (http)")
    except ConnectionError:
        print("Warning: Failed to close the http tunnel")

    try:
        _ = requests.delete("http://localhost:4040/api/tunnels/relay_tunnel")
    except ConnectionError:
        print("Warning: Failed to close the https tunnel")

    # join to shut down observer thread gracefully
    observer.join()


if __name__ == "__main__":

    web_server, nbconvert = start_services()
    watchdog = start_watchdog()

    try:
        while True:
            time.sleep(20)
    except KeyboardInterrupt:  # end the relay with interrupt
        shutdown(web_server, watchdog)
