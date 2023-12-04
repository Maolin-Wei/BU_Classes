from PyQt5 import QtWidgets, uic
import sys
from database import DatabaseManager


class RegisterWindow(QtWidgets.QDialog):
    def __init__(self, login_window):
        super(RegisterWindow, self).__init__()
        uic.loadUi('./ui/register.ui', self)
        self.login_window = login_window
        self.db_manager = DatabaseManager('database.db')
        self.db_manager.connect()
        try:
            self.registerButton.clicked.connect(self.handleRegister)
        except Exception as e:
            print(e)

    def handleRegister(self):
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()

        if self.db_manager.is_username_exist(username):
            QtWidgets.QMessageBox.warning(self, 'Error', 'Username already taken')
            return

        self.db_manager.add_user(username, password)

        QtWidgets.QMessageBox.information(self, 'Success', 'Account created successfully')
        self.close()
        self.login_window.showLogin()

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    register = RegisterWindow()
    register.show()
    sys.exit(app.exec_())
