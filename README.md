# aiolink


disclaimer: this is a hack.


it was created with main purpose of allowing a threadless cpython to interact simply with a javascript engine.

second thing is : it works and allow to write cool stuff directly in python like

```
window.alert('hello world')

window.document.title = "why should I have thrown javascript before"

window.document.getElementById('exit_label').textContent =  "this way out"

```

maybe later implement callbacks for event bubble system of the browser Dom


