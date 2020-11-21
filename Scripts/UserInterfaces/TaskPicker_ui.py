# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TaskPicker.ui'
##
## Created by: Qt User Interface Compiler version 5.15.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_dlg_PickTask(object):
    def setupUi(self, dlg_PickTask):
        if not dlg_PickTask.objectName():
            dlg_PickTask.setObjectName(u"dlg_PickTask")
        dlg_PickTask.resize(218, 143)
        dlg_PickTask.setSizeGripEnabled(False)
        dlg_PickTask.setModal(False)
        self.verticalLayout_2 = QVBoxLayout(dlg_PickTask)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(dlg_PickTask)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.verticalLayout_2.addWidget(self.label)

        self.task_Box = QComboBox(dlg_PickTask)
        self.task_Box.setObjectName(u"task_Box")

        self.verticalLayout_2.addWidget(self.task_Box)

        self.label_2 = QLabel(dlg_PickTask)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)

        self.status_Box = QComboBox(dlg_PickTask)
        self.status_Box.setObjectName(u"status_Box")

        self.verticalLayout_2.addWidget(self.status_Box)

        self.cb_preview = QCheckBox(dlg_PickTask)
        self.cb_preview.setObjectName(u"cb_preview")
        self.cb_preview.setChecked(True)

        self.verticalLayout_2.addWidget(self.cb_preview)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_publish = QPushButton(dlg_PickTask)
        self.btn_publish.setObjectName(u"btn_publish")

        self.horizontalLayout.addWidget(self.btn_publish)

        self.btn_cancel = QPushButton(dlg_PickTask)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.horizontalLayout.addWidget(self.btn_cancel)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.retranslateUi(dlg_PickTask)

        self.btn_publish.setDefault(True)


        QMetaObject.connectSlotsByName(dlg_PickTask)
    # setupUi

    def retranslateUi(self, dlg_PickTask):
        dlg_PickTask.setWindowTitle(QCoreApplication.translate("dlg_PickTask", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("dlg_PickTask", u"Pick what task to publish to:", None))
        self.label_2.setText(QCoreApplication.translate("dlg_PickTask", u"Set status to:", None))
        self.cb_preview.setText(QCoreApplication.translate("dlg_PickTask", u"Set image as preview", None))
        self.btn_publish.setText(QCoreApplication.translate("dlg_PickTask", u"Publish", None))
        self.btn_cancel.setText(QCoreApplication.translate("dlg_PickTask", u"Cancel", None))
    # retranslateUi

