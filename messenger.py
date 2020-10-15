from requests import get, post, exceptions
from datetime import datetime

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from client_commands import *
from client_content import *
from clicklabel import clickable
from client_ui import Ui_Messenger


class MessengerWindow(QtWidgets.QMainWindow, Ui_Messenger):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._translate = QtCore.QCoreApplication.translate

        self.sendButton.pressed.connect(self.send)
        self.signUpButton.pressed.connect(self.signUpUser)
        self.loginButton.pressed.connect(self.loginUser)

        self.actionShortcuts.triggered.connect(self.showShortcutsBox)
        self.actionCommands.triggered.connect(self.showCommandsBox)
        self.actionAbout.triggered.connect(self.showAboutBox)
        self.actionContacts.triggered.connect(self.showContactsBox)
        self.actionLogout.triggered.connect(self.logout)
        self.actionClose.triggered.connect(self.close)

        self.textEdit.installEventFilter(self)
        self.last_message_time = 0
        self.username = None
        self.password = None
        self.warningMessages = {
            "emptyStr": '<html><head/><body><p><br/></p></body></html>',
            "registered": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Username '
                          'is already registered</span></p></body></html> ',
            "loginRequired": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Login is '
                             'required</span></p></body></html>',
            "invalidLogin": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Username '
                            'doesn\'t exist</span></p></body></html> ',
            "loginOutOfRange": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Username '
                               'must be between 4 and 20 in length</span></p></body></html> ',
            "passwordRequired": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Password is '
                                'required</span></p></body></html> ',
            "invalidPassword": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Password '
                               'doesn\'t match</span></p></body></html> ',
            "passwordOutOfRange": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Password '
                                  'must be between 4 and 20 in length</span></p></body></html> ',
            "notAlphanumeric": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Login can '
                               'only contain alphanumeric characters</span></p></body></html>',
            "banned": '<html><head/><body><p><span style=" font-style:italic; color:#ef2929;">Account '
                      'was banned</span></p></body></html>',
        }
        self.messageBoxText = getMessageBoxText()
        self.client_commands = [
            {'name': 'close', 'description': 'Close the messenger',
             'detailed': '#Usage: /close\n'
                         'Ask you to close messenger.'},
            {'name': 'logout', 'description': 'Logout account',
             'detailed': '#Usage: /logout\n'
                         'Ask you to logout account.'},
            {'name': 'reload', 'description': 'Clear commands messages',
             'detailed': '#Usage: /reload\n'
                         'Clear all commands` messages.'},
        ]
        self.run_client_command = {'close': self.close,
                                   'logout': self.logout,
                                   'reload': self.reload}
        self.server_commands = []
        self.run_server_command = {}
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.getUpdates)
        self.timer.start(1000)
        clickable(self.signUpLabel).connect(self.goToRegistration)
        clickable(self.loginLabel).connect(self.goToLogin)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and obj is self.textEdit:
            if event.key() == QtCore.Qt.Key_Return and self.textEdit.hasFocus():
                self.send()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit', self.messageBoxText["close"],
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            try:
                post(
                    'http://127.0.0.1:5000/logout',
                    json={"username": self.username}, verify=False
                )
            except exceptions.RequestException as e:
                print(e)
                raise SystemExit

            event.accept()
        else:
            event.ignore()

    def logout(self):
        reply = QMessageBox.question(self, 'Logout', self.messageBoxText["logout"],
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            try:
                post(
                    'http://127.0.0.1:5000/logout',
                    json={"username": self.username}, verify=False
                )
            except exceptions.RequestException as e:
                print(e)
                self.showServerOffBox()
                self.clearUserData()
                return

            self.goToLogin()
            self.clearUserData()
            self.actionLogout.setEnabled(False)
        else:
            return

    def clearUserData(self):
        self.username = None
        self.textEdit.clear()
        self.textBrowser.clear()
        self.last_message_time = 0

    def reload(self):
        self.textBrowser.clear()
        self.last_message_time = 0

    def goToRegistration(self):
        self.stackedWidget.setCurrentIndex(1)

    def goToLogin(self):
        self.stackedWidget.setCurrentIndex(0)

    def clearCredentials(self):
        self.passwordLine1.clear()
        self.loginLine1.clear()
        self.passwordLine2.clear()
        self.loginLine2.clear()
        self.password = None

    def showAboutBox(self):
        QMessageBox.information(self, 'About', self.messageBoxText["about"])

    def showContactsBox(self):
        QMessageBox.information(self, 'Contacts', self.messageBoxText["contacts"])

    def showServerOffBox(self):
        QMessageBox.critical(self, 'Opsss...', self.messageBoxText["serverIsOff"])
        self.goToLogin()

    def showShortcutsBox(self):
        QMessageBox.information(self, 'Shortcuts', self.messageBoxText["shortcuts"])

    def showCommandsBox(self):
        QMessageBox.information(self, 'Commands', self.messageBoxText["commands"])

    def signUpUser(self):
        self.loginError2.setText(self._translate("Messenger", self.warningMessages['emptyStr']))
        self.passwordError2.setText(self._translate("Messenger", self.warningMessages['emptyStr']))
        self.loginLine2.setStyleSheet("border: 1px solid #B8B5B2")
        self.passwordLine2.setStyleSheet("border: 1px solid #B8B5B2")
        self.username = self.loginLine2.text()
        self.password = self.passwordLine2.text()

        if not self.username:
            if not self.password:
                self.loginError2.setText(self._translate("Messenger", self.warningMessages['loginRequired']))
                self.passwordError2.setText(self._translate("Messenger", self.warningMessages['passwordRequired']))
                self.loginLine2.setStyleSheet("border: 1px solid red")
                self.passwordLine2.setStyleSheet("border: 1px solid red")
                return
            else:
                self.loginError2.setText(self._translate("Messenger", self.warningMessages['loginRequired']))
                self.loginLine2.setStyleSheet("border: 1px solid red")
                return
        else:
            if not self.password:
                self.passwordError2.setText(self._translate("Messenger", self.warningMessages['passwordRequired']))
                self.passwordLine2.setStyleSheet("border: 1px solid red")
                return

        if not self.username.isalnum():
            self.loginError2.setText(self._translate("Messenger", self.warningMessages['notAlphanumeric']))
            self.loginError2.adjustSize()
            self.loginLine2.setStyleSheet("border: 1px solid red")
            return

        try:
            response = post(
                'http://127.0.0.1:5000/signup',
                auth=(self.username, self.password),
                verify=False
            )
        except exceptions.RequestException as e:
            print(e)
            self.showServerOffBox()
            self.clearCredentials()
            return

        if response.json()['loginOutOfRange']:
            self.loginError2.setText(self._translate("Messenger", self.warningMessages['loginOutOfRange']))
            self.loginError2.adjustSize()
            self.loginLine2.setStyleSheet("border: 1px solid red")
            return
        elif response.json()['passwordOutOfRange']:
            self.passwordError2.setText(self._translate("Messenger", self.warningMessages['passwordOutOfRange']))
            self.passwordError2.adjustSize()
            self.passwordLine2.setStyleSheet("border: 1px solid red")
            return
        elif not response.json()['ok']:
            self.loginError2.setText(self._translate("Messenger", self.warningMessages['registered']))
            self.loginError2.adjustSize()
            self.loginLine2.setStyleSheet("border: 1px solid red")
            return

        self.getServerCommands()
        self.stackedWidget.setCurrentIndex(2)
        self.actionLogout.setEnabled(True)
        self.clearCredentials()

    def loginUser(self):
        self.loginError1.setText(self._translate("Messenger", self.warningMessages['emptyStr']))
        self.passwordError1.setText(self._translate("Messenger", self.warningMessages['emptyStr']))
        self.loginLine1.setStyleSheet("border: 1px solid #B8B5B2")
        self.passwordLine1.setStyleSheet("border: 1px solid #B8B5B2")
        self.username = self.loginLine1.text()
        self.password = self.passwordLine1.text()

        if not self.username:
            if not self.password:
                self.loginError1.setText(self._translate("Messenger", self.warningMessages['loginRequired']))
                self.passwordError1.setText(self._translate("Messenger", self.warningMessages['passwordRequired']))
                self.loginLine1.setStyleSheet("border: 1px solid red")
                self.passwordLine1.setStyleSheet("border: 1px solid red")
                return
            else:
                self.loginError1.setText(self._translate("Messenger", self.warningMessages['loginRequired']))
                self.loginLine1.setStyleSheet("border: 1px solid red")
                return
        else:
            if not self.password:
                self.passwordError1.setText(self._translate("Messenger", self.warningMessages['passwordRequired']))
                self.passwordLine1.setStyleSheet("border: 1px solid red")
                return

        try:
            response = post(
                'http://127.0.0.1:5000/auth',
                auth=(self.username, self.password),
                verify=False
            )
        except exceptions.RequestException as e:
            print(e)
            self.showServerOffBox()
            self.clearCredentials()
            return

        if not response.json()['exist']:
            self.loginError1.setText(self._translate("Messenger", self.warningMessages['invalidLogin']))
            self.loginLine1.setStyleSheet("border: 1px solid red")
            return
        if not response.json()['match']:
            self.passwordError1.setText(self._translate("Messenger", self.warningMessages['invalidPassword']))
            self.passwordLine1.setStyleSheet("border: 1px solid red")
            return
        if response.json()['banned']:
            self.loginError1.setText(self._translate("Messenger", self.warningMessages['banned']))
            self.loginLine1.setStyleSheet("border: 1px solid red")
            return

        self.getServerCommands()
        self.stackedWidget.setCurrentIndex(2)
        self.actionLogout.setEnabled(True)
        self.clearCredentials()

    def getServerCommands(self):
        try:
            response = post(
                'http://127.0.0.1:5000/command',
                json={"username": self.username, "command": 'help'}, verify=False
            )
        except exceptions.RequestException as e:
            print(e)
            self.clearUserData()
            self.showServerOffBox()
            return

        if not response.json()['ok']:
            self.addText(response.json()['output'] + "\n")
            self.textEdit.clear()
            return

        self.server_commands = response.json()['output']

        for cmd in self.server_commands:
            if cmd['name'] != 'help': self.run_server_command[f"{cmd['name']}"] = globals()[cmd['name']]

    def send(self):
        text = self.textEdit.toPlainText()
        text = text.strip()

        if not text:
            return
        elif text.startswith('/'):
            self.sendCommand(text[1:])
        else:
            self.sendMessage(text)

    def sendMessage(self, text):
        try:
            post(
                'http://127.0.0.1:5000/send',
                json={"username": self.username, "text": text},
                verify=False
            )
        except exceptions.RequestException as e:
            print(e)
            self.clearUserData()
            self.showServerOffBox()
            return

        self.textEdit.clear()
        self.textEdit.repaint()

    def sendCommand(self, cmd_string):
        command = cmd_string.split()[0]
        args = cmd_string.split()[1:] if len(cmd_string) > 1 else None

        if command in [cmd['name'] for cmd in self.client_commands]:
            self.run_client_command.get(command)()
            self.textEdit.clear()
            return

        elif command not in [cmd['name'] for cmd in self.server_commands]:
            self.addText(f"Error: Command '/{command}' not found.\n"
                         f"Try '/help' to list all available commands :)\n")
            self.textEdit.clear()
            return

        elif command == 'help':
            output = helpClient(self.client_commands, self.server_commands, args)
            self.addText(output)
            self.textEdit.clear()
            return

        try:
            response = post(
                'http://127.0.0.1:5000/command',
                json={"username": self.username, "command": cmd_string}, verify=False
            )
        except exceptions.RequestException as e:
            print(e)
            self.clearUserData()
            self.showServerOffBox()
            return

        if not response.json()['ok']:
            self.addText("Error: " + response.json()['output'] + "\n")
            self.textEdit.clear()
            return

        run_command = self.run_server_command.get(command)
        output = run_command(response.json()['output'], args)

        self.addText(output)
        self.textEdit.clear()
        self.textEdit.repaint()

    def getUpdates(self):
        if not self.stackedWidget.currentIndex() == 2:
            return

        try:
            response = get(
                'http://127.0.0.1:5000/messages',
                params={'after': self.last_message_time},
                verify=False
            )
            data = response.json()
        except exceptions.RequestException as e:
            print(e)
            self.clearUserData()
            self.showServerOffBox()
            return

        for message in data['messages']:
            # float -> datetime
            beauty_time = datetime.fromtimestamp(message['time'])
            beauty_time = beauty_time.strftime('%Y/%m/%d %H:%M:%S')

            self.addText(message['username'] + ' ' + beauty_time)
            self.addText(message['text'] + "\n")
            self.last_message_time = message['time']

    def addText(self, text):
        self.textBrowser.append(text)
        self.textBrowser.repaint()


app = QtWidgets.QApplication([])
window = MessengerWindow()
window.show()
app.exec_()
