try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *

except:
    from PySide.QtCore import *
    from PySide.QtGui import *

import TaskPicker_ui

from PrismUtils.Decorators import err_catcher


class TaskPicker(QDialog, TaskPicker_ui.Ui_dlg_PickTask):
    def __init__(self, core, taskTypes_dicts):
        QDialog.__init__(self)
        self.setupUi(self)

        self.core = core
        self.populateTasks(taskTypes_dicts)
        self.picked_data = None

        # self.loadData()
        self.connectEvents()

    @err_catcher(name=__name__)
    def populateTasks(self, taskTypes_dicts):
        for typeTask in taskTypes_dicts:
            self.task_Box.addItem(str(typeTask["name"]),
                                  typeTask)

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.btn_publish.clicked.connect(self.publish)
        self.btn_cancel.clicked.connect(self.cancel)

    @err_catcher(name=__name__)
    def publish(self):
        self.picked_data = self.task_Box.itemData(
            self.task_Box.currentIndex())
        self.accept()

    @err_catcher(name=__name__)
    def cancel(self):
        self.picked_data = None
        self.reject()

    @err_catcher(name=__name__)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.publish()
        elif event.key() == Qt.Key_Escape:
            self.reject()
