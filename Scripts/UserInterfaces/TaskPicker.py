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
    def __init__(self, core, taskTypes_dicts, taskStatuses_dicts, doStatus):
        QDialog.__init__(self)
        self.setupUi(self)

        self.core = core
        self.populateTasks(taskTypes_dicts, taskStatuses_dicts)
        self.status_Box
        self.picked_data = None
        self.doStatus = doStatus
        if self.doStatus is False:
            self.status_Box.setVisible(False)
            self.cb_preview.setVisible(False)
        # self.loadData()
        self.connectEvents()

    @err_catcher(name=__name__)
    def populateTasks(self, taskTypes_dicts, taskStatuses_dicts):
        for taskType in taskTypes_dicts:
            self.task_Box.addItem(str(taskType["name"]),
                                  taskType)

        self.status_Box.addItem("[Keep as current]", None)
        for taskStatus in taskStatuses_dicts:
            self.status_Box.addItem(str(taskStatus["name"]), taskStatus)

    @ err_catcher(name=__name__)
    def connectEvents(self):
        self.btn_publish.clicked.connect(self.publish)
        self.btn_cancel.clicked.connect(self.cancel)

    @ err_catcher(name=__name__)
    def publish(self):
        if self.doStatus is True:
            self.picked_data = [
                self.task_Box.itemData(self.task_Box.currentIndex()),
                self.status_Box.itemData(self.status_Box.currentIndex()),
                self.cb_preview.isChecked(),
                self.comment_Text.toPlainText()
            ]
        else:
            self.picked_data = self.task_Box.itemData(
                self.task_Box.currentIndex())
        self.accept()

    @ err_catcher(name=__name__)
    def cancel(self):
        if self.doStatus is True:
            self.picked_data = [None, None, None, None]
        else:
            self.picked_data = None
        self.reject()

    @ err_catcher(name=__name__)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.publish()
        elif event.key() == Qt.Key_Escape:
            self.reject()
