import urwid
import re

class GameInProgressBox(urwid.WidgetWrap):
    def __init__(self, pile):
        super(GameInProgressBox, self).__init__(pile)

        #[urwid.Text(u'This is a test 1'), urwid.Text(u'This is a test 2'), ]

def exit_on_q(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


pile = urwid.Pile([('pack', urwid.Text(u'This is a test 1')), ('pack', urwid.Text(u'This is a test 2')), ])
urwid.MainLoop(GameInProgressBox(pile), unhandled_input=exit_on_q).run()
