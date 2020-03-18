#!/usr/bin/env python
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout


buffer1 = Buffer()  # Editable buffer.

outwin = Window(content=FormattedTextControl(text='Hello world'))

root_container = VSplit([
    # One window that holds the BufferControl with the default buffer on
    # the left.
    Window(content=BufferControl(buffer=buffer1)),

    # A vertical line in the middle. We explicitly specify the width, to
    # make sure that the layout engine will not try to divide the whole
    # width by three for all these windows. The window will simply fill its
    # content by repeating this character.
    Window(width=1, char='|'),

    # Display the text 'Hello world' on the right.
    outwin
])

kb = KeyBindings()

@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call.
    """
    event.app.exit()

@kb.add('c-t')
def tree_(event):
    """
    Pressing Ctrl-T will tree /tmp

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call.
    """

    print(dir(outwin))


layout = Layout(root_container)

app = Application(key_bindings = kb, layout=layout, full_screen=True)
app.run() # You won't be able to Exit this app