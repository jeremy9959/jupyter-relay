## jupyter relay

This is a small piece of code that watches an ipynb file, and, when it changes,
converts it to html and posts it to a web server.

It exploits [ngrok](http://ngrok.com) to forward the web server to a cloud endpoint.

This was developed for teaching purposes so that students can see on their own
machine what the instructor has entered into the notebook.

It relies on:

- flask
- ngrok
- gunicorn
- nbconvert

To install it, put relay.py and simple_flask.py in a directory.  Start ngrok (if it isn't already running)
with 

```bash
$ ~/ngrok start --none &
``` 

Then to start the relay:

```bash
$ python relay.py file.ipynb
Relay will be available at:
 https://5ab68708.ngrok.io
writing to /tmp/relay.html
```

The link reported can be shared with the class to view the notebook.

Use CTRL-C to quit and shut everything down.
