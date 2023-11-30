from PyQt5 import QtWidgets, uic
import sys
from gui_main import MainWindow
from register import RegisterWindow
from database import DatabaseManager


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super(LoginWindow, self).__init__()
        uic.loadUi('./ui/login.ui', self)

        self.registerWindow = None
        self.passwordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)

        self.db_manager = DatabaseManager('database.db')
        self.db_manager.connect()

        self.loginButton.clicked.connect(self.handleLogin)
        self.registerButton.clicked.connect(self.registerAccount)

    def showLogin(self):
        self.show()

    def registerAccount(self):
        self.hide()
        self.registerWindow = RegisterWindow(self)
        self.registerWindow.show()

    def handleLogin(self):
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()

        if self.db_manager.validate_login(username, password):
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Wrong username or password')

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    login = LoginWindow()

    if login.exec_() == QtWidgets.QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
