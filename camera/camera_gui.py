import sys
from PyQt5.QtWidgets import *

class CameraApp(QWidget):

	def __init__(self):
		super().__init__()
		self.initUI()


	def initUI(self):

		self.setGeometry(200, 200, 900, 600)
		self.setWindowTitle('Camera GUI')
		free_run_button = QPushButton('Free Run', self)
		base_line_button = QPushButton('Calculate Baseline', self)
		draw_button = QPushButton('Draw Polygon', self)
		free_run_button.move(25,50)
		base_line_button.move(25,80)
		draw_button.move(25,110)
		self.show()

if __name__ == '__main__':

	app = QApplication(sys.argv)
	ex = CameraApp()
	sys.exit(app.exec_())