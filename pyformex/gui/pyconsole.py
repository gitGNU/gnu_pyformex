# $Id$
##
##  This file is part of pyFormex 0.9.1  (Tue Oct 15 21:05:25 CEST 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2013 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
##  Distributed under the GNU General Public License version 3 or later.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##
"""Interactive Python interpreter for pyFormex.

"""
from __future__ import print_function

import os
import re
import sys
import readline
import atexit
import traceback


from gui import QtGui, QtCore
from gui.guimain import Board
import utils


##########################################################################

class PyConsole(QtGui.QPlainTextEdit):
    def __init__(self,interpreter=None,prompt='>>> ',startup_message='pyFormex interactive Python console (EXPERIMENTAL!)',parent=None):
        super(PyConsole, self).__init__(parent)
        self.prompt = prompt
        self.history = []
        self.construct = []
        if interpreter is None:
            import code
            import script
            interpreter = code.InteractiveInterpreter(script.Globals())
        self.interpreter = interpreter

        self.boardmode = False

        #self.setGeometry(50, 75, 600, 400)
        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.setUndoRedoEnabled(False)
        self.document().setDefaultFont(QtGui.QFont("monospace", 10, QtGui.QFont.Normal))
        self.showMessage(startup_message)



    def write(self,s,color=None):
        self.appendPlainText(s+'\n')
        #self.showMessage(s)


    def flush(self):
        self.update()


    def redirect(self, onoff):
        """Redirect standard and error output to this message board"""
        if onoff:
            sys.stderr.flush()
            sys.stdout.flush()
            self.stderr = sys.stderr
            self.stdout = sys.stdout
            sys.stderr = self
            sys.stdout = self
        else:
            if self.stderr:
                sys.stderr = self.stderr
            if self.stdout:
                sys.stdout = self.stdout
            self.stderr = None
            self.stdout = None


    def showMessage(self, message):
        self.appendPlainText(message)
        self.showPrompt()


    def showPrompt(self):
        if self.construct:
            prompt = '.'*(len(self.prompt)-1) + ' '
        else:
            prompt = self.prompt
        self.appendPlainText(prompt)
        self.moveCursor(QtGui.QTextCursor.End)


    def getCommand(self):
        doc = self.document()
        curr_line = unicode(doc.findBlockByLineNumber(doc.lineCount() - 1).text())
        curr_line = curr_line.rstrip()
        curr_line = curr_line[len(self.prompt):]
        return curr_line


    def setCommand(self, command):
        if self.getCommand() == command:
            return
        self.moveCursor(QtGui.QTextCursor.End)
        self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
        for i in range(len(self.prompt)):
            self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
        self.textCursor().removeSelectedText()
        self.textCursor().insertText(command)
        self.moveCursor(QtGui.QTextCursor.End)


    def getConstruct(self, command):
        if self.construct:
            prev_command = self.construct[-1]
            self.construct.append(command)
            if not prev_command and not command:
                ret_val = '\n'.join(self.construct)
                self.construct = []
                return ret_val
            else:
                return ''
        else:
            if command and command[-1] == (':'):
                self.construct.append(command)
                return ''
            else:
                return command

    def getHistory(self):
        return self.history

    def setHisory(self, history):
        self.history = history

    def addToHistory(self, command):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = len(self.history)

    def getPrevHistoryEntry(self):
        if self.history:
            self.history_index = max(0, self.history_index - 1)
            return self.history[self.history_index]
        return ''

    def getNextHistoryEntry(self):
        if self.history:
            hist_len = len(self.history)
            self.history_index = min(hist_len, self.history_index + 1)
            if self.history_index < hist_len:
                return self.history[self.history_index]
        return ''

    def getCursorPosition(self):
        return self.textCursor().columnNumber() - len(self.prompt)

    def setCursorPosition(self, position):
        self.moveCursor(QtGui.QTextCursor.StartOfLine)
        for i in range(len(self.prompt) + position):
            self.moveCursor(QtGui.QTextCursor.Right)


    ## def runSource(self,command):
    ##     try:
    ##         print("EVAL")
    ##         result = eval(command, self.namespace, self.namespace)
    ##         if result != None:
    ##             self.appendPlainText(repr(result))
    ##     except SyntaxError:
    ##         print("EXEC")
    ##         exec command in self.namespace


    ## def runSource(self,command):
    ##     try:
    ##         print("EVAL")
    ##         res = self.interpreter.runsource(command,'<console>','eval')
    ##         print("RES=%s" % res)
    ##     except SyntaxError:
    ##         print("EXEC")
    ##         res = self.interpreter.runsource(command,'<console>','single')
    ##         print("RES=%s" % res)


    def runSource(self, command):
        res = self.interpreter.runsource(command, '<console>', 'single')


    def runCommand(self):
        command = self.getCommand()
        self.addToHistory(command)

        command = self.getConstruct(command)

        if command:
            tmp_stdout = sys.stdout

            class stdoutProxy():
                def __init__(self, write_func):
                    self.write_func = write_func
                    self.skip = False

                def write(self, text):
                    if not self.skip:
                        stripped_text = text.rstrip('\n')
                        self.write_func(stripped_text)
                        QtCore.QCoreApplication.processEvents()
                    self.skip = not self.skip

            sys.stdout = stdoutProxy(self.appendPlainText)
            try:
                self.runSource(command)
            except SystemExit:
                self.close()
            except:
                traceback_lines = traceback.format_exc().split('\n')
                # Remove traceback mentioning this file, and a linebreak
                for i in (3, 2, 1, -1):
                    traceback_lines.pop(i)
                self.appendPlainText('\n'.join(traceback_lines))
            sys.stdout = tmp_stdout
        self.showPrompt()

    def keyPressEvent(self, event):
        if self.boardmode:
            return
        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.runCommand()
            return
        if event.key() == QtCore.Qt.Key_Home:
            self.setCursorPosition(0)
            return
        if event.key() == QtCore.Qt.Key_PageUp:
            return
        elif event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
            if self.getCursorPosition() == 0:
                return
        elif event.key() == QtCore.Qt.Key_Up:
            self.setCommand(self.getPrevHistoryEntry())
            return
        elif event.key() == QtCore.Qt.Key_Down:
            self.setCommand(self.getNextHistoryEntry())
            return
        elif event.key() == QtCore.Qt.Key_D and event.modifiers() == QtCore.Qt.ControlModifier:
            self.close()
        super(PyConsole, self).keyPressEvent(event)


##########################################################################



class OtherPyConsole(Board):

    def __init__(self,parent=None):

        super(PyConsole, self).__init__(parent)
        self.setReadOnly(False)

        self.refreshMarker = False # to change back to >>> from ...
        self.multiLine = False # code spans more than one line
        self.command = '' # command to be ran
        self.history = [] # list of commands entered
        self.historyIndex = -1
        self.interpreterLocals = {}

        # initialize interpreter with self locals
        interpreterLocals = locals()
        if interpreterLocals:
            # when we pass in locals, we don't want it to be named "self"
            # so we rename it with the name of the class that did the passing
            # and reinsert the locals back into the interpreter dictionary
            selfName = interpreterLocals['self'].__class__.__name__
            interpreterLocalVars = interpreterLocals.pop('self')
            self.interpreterLocals[selfName] = interpreterLocalVars
        else:
            self.interpreterLocals = interpreterLocals
        self.interpreter = InteractiveInterpreter(self.interpreterLocals)


    def write(self,s,color=None):
        """Write a string to the message board.

        If a color is specified, the text is shown in the specified
        color, but the default board color remains unchanged.
        """
        if color:
            savecolor = self.textColor()
            self.setTextColor(QtGui.QColor(color))
        else:
            savecolor = None
        # A single blank character seems to be generated by a print
        # instruction containing a comma: skip it
        if s == ' ':
            return
        #self.buffer += '[%s:%s]' % (len(s),s)
        if len(s) > 0:
            if not s.endswith('\n'):
                s += '\n'
            self.insertPlainText(s)
            self.cursor.movePosition(QtGui.QTextCursor.End)
        if savecolor:
            self.setTextColor(savecolor)
        self.ensureCursorVisible()


    def printBanner(self):
        self.write(sys.version)
        self.write(' on ' + sys.platform + '\n')
        msg = 'Type !hist for a history view and !hist(n) history index recall'
        self.write(msg + '\n')


    def marker(self):
        if self.multiLine:
            self.insertPlainText('... ')
        else:
            self.insertPlainText('>>> ')


    def clearCurrentBlock(self):
        # block being current row
        length = len(self.document().lastBlock().text()[4:])
        if length == 0:
            return None
        else:
            # should have a better way of doing this but I can't find it
            [self.textCursor().deletePreviousChar() for x in xrange(length)]
        return True

    def recallHistory(self):
        # used when using the arrow keys to scroll through history
        self.clearCurrentBlock()
        if self.historyIndex != -1:
            self.insertPlainText(self.history[self.historyIndex])
        return True

    def customCommands(self, command):

        if command == '!hist': # display history
            self.append('') # move down one line
            # vars that are in the command are prefixed with ____CC and deleted
            # once the command is done so they don't show up in dir()
            backup = self.interpreter.locals.copy()
            history = self.history[:]
            history.reverse()
            for i, x in enumerate(history):
                iSize = len(str(i))
                delta = len(str(len(history))) - iSize
                line = line = ' ' * delta + '%i: %s' % (i, x) + '\n'
                self.write(line)
            self.interpreter.locals = backup
            return True
        import re
        if re.match('!hist\(\d+\)', command): # recall command from history
            backup = self.interpreter.locals.copy()
            history = self.history[:]
            history.reverse()
            index = int(command[6:-1])
            self.clearCurrentBlock()
            command = history[index]
            if command[-1] == ':':
                self.multiLine = True
            self.write(command)
            self.interpreter.locals = backup
            return True

        return False

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Escape:
            # proper exit
            self.interpreter.runsource('exit()')

        ## if event.key() == QtCore.Qt.Key_Down:
        ##     if self.historyIndex == len(self.history):
        ##         self.historyIndex -= 1
        ##     try:
        ##         if self.historyIndex > -1:
        ##             self.historyIndex -= 1
        ##             self.recallHistory()
        ##         else:
        ##             self.clearCurrentBlock()
        ##     except:
        ##         pass
        ##     return None

        ## if event.key() == QtCore.Qt.Key_Up:
        ##     try:
        ##         if len(self.history) - 1 > self.historyIndex:
        ##             self.historyIndex += 1
        ##             self.recallHistory()
        ##         else:
        ##             self.historyIndex = len(self.history)
        ##     except:
        ##         pass
        ##     return None

        if event.key() == QtCore.Qt.Key_Home:
            # set cursor to position 4 in current block. 4 because that's where
            # the marker stops
            blockLength = len(self.document().lastBlock().text()[4:])
            lineLength = len(self.document().toPlainText())
            position = lineLength - blockLength
            textCursor = self.textCursor()
            textCursor.setPosition(position)
            self.setTextCursor(textCursor)
            return None

        if event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace]:
            # don't allow deletion of marker
            if self.textCursor().positionInBlock() == 4:
                return None

        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            # set cursor to end of line to avoid line splitting
            textCursor = self.textCursor()
            position = len(self.document().toPlainText())
            textCursor.setPosition(position)
            self.setTextCursor(textCursor)

            line = str(self.document().lastBlock().text())[4:] # remove marker
            line.rstrip()
            self.historyIndex = -1

            if self.customCommands(line):
                return None
            else:
                try:
                    line[-1]
                    self.haveLine = True
                    if line[-1] == ':':
                        self.multiLine = True
                    self.history.insert(0, line)
                except:
                    self.haveLine = False

                if self.haveLine and self.multiLine: # multi line command
                    self.command += line + '\n' # + command and line
                    self.append('') # move down one line
                    self.marker() # handle marker style
                    return None

                if self.haveLine and not self.multiLine: # one line command
                    self.command = line # line is the command
                    self.append('') # move down one line
                    self.interpreter.runsource(self.command)
                    self.command = '' # clear command
                    self.marker() # handle marker style
                    return None

                if self.multiLine and not self.haveLine: # multi line done
                    self.append('') # move down one line
                    self.interpreter.runsource(self.command)
                    self.command = '' # clear command
                    self.multiLine = False # back to single line
                    self.marker() # handle marker style
                    return None

                if not self.haveLine and not self.multiLine: # just enter
                    self.append('')
                    self.marker()
                    return None
                return None

        # allow all other key events
        super(PyConsole, self).keyPressEvent(event)

# End
