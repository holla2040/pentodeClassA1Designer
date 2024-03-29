#!/usr/bin/env python3

# https://www.pythonguis.com/tutorials/plotting-matplotlib/

import sys,time,random,matplotlib,subprocess,csv
from rawread import rawread
from pprint import pprint
import numpy as np

matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QDial, QDoubleSpinBox, QLabel, QMainWindow, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QLineEdit, QLayout, QComboBox, QWidget, QCheckBox)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height),tight_layout=True,linewidth=0.1)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.running = False
        self.ylim = []
        self.setWindowTitle("Pentode Designer")
        self.xmax = 500
        self.xmaxlast = 500

        f = open('tubes.csv','r')
        rows = csv.DictReader(f)
        self.tubes = {row['name']:row for row in rows} # list

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.mpl_connect('button_press_event', self.measureBegin)
        self.canvas.mpl_connect('button_release_event', self.measureEnd)

        layout = QVBoxLayout()

        toolbar = QHBoxLayout()
        l1 = QVBoxLayout()
        self.partnumber = QComboBox()
        self.partnumber.addItems([key for key in sorted(self.tubes.keys())])
        self.partnumber.setCurrentIndex(12)
        l1.addWidget(self.partnumber)

        l2 = QHBoxLayout()
        l2.addWidget(QLabel("Plate Dissipation"))
        self.plateDissipationLabel = QLineEdit("17")
        self.plateDissipationLabel.setFixedWidth(50)
        self.plateDissipationLabel.returnPressed.connect(self.updatePlateDissipation)
        self.updatePlateDissipation()
        l2.addWidget(self.plateDissipationLabel)
        l1.addLayout(l2,0)

        l3 = QHBoxLayout()
        l3.addWidget(QLabel("Autoscale Y"))
        self.autoscale = QCheckBox()
        self.autoscale.setChecked(True)
        self.autoscale.toggled.connect(self.updateResults)
        l3.addWidget(self.autoscale)
        l1.addLayout(l3,0)


        buttonQuit = QPushButton("Quit", self)
        buttonQuit.clicked.connect(self.onQuit)
        l1.addWidget(buttonQuit)
        toolbar.addLayout(l1,0)

        labels = QVBoxLayout()
        l = QLabel("Vplate")
        l.setFixedHeight(20)
        labels.addWidget(l)

        self.lbiasi = QLabel("Iplate@Vplate")
        self.lbiasi.setFixedHeight(20)
        labels.addWidget(self.lbiasi)

        l = QLabel("Vscreen")
        l.setFixedHeight(20)
        labels.addWidget(l)

        l = QLabel("Load Impedance")
        l.setFixedHeight(20)
        labels.addWidget(l)

        '''
        l = QLabel("hi")
        l.setFixedHeight(20)
        labels.addWidget(l)
        '''
        l4 = QHBoxLayout()
        l4.addWidget(QLabel("Inductive"))
        self.inductive = QCheckBox()
        self.inductive.setChecked(True)
        self.inductive.toggled.connect(self.inductiveChanged)
        l4.addWidget(self.inductive)
        labels.addLayout(l4)

        toolbar.addLayout(labels,0)

        values = QVBoxLayout()
        self.supplyVoltageLabel = QLineEdit("250")
        self.supplyVoltageLabel.setFixedWidth(60)
        self.supplyVoltageLabel.setFixedHeight(20)

        self.biasCurrentLabel = QLineEdit("0.01")
        self.biasCurrentLabel.setFixedWidth(60)
        self.biasCurrentLabel.setFixedHeight(20)

        self.screenVoltageLabel = QLineEdit("600")
        self.screenVoltageLabel.setFixedWidth(60)
        self.screenVoltageLabel.setFixedHeight(20)

        self.loadImpedanceLabel = QLineEdit("4500")
        self.loadImpedanceLabel.setFixedWidth(60)

        spacer = QLabel("Results")
        spacer.setFixedHeight(20)

        values.addWidget(self.supplyVoltageLabel)
        values.addWidget(self.biasCurrentLabel)
        values.addWidget(self.screenVoltageLabel)
        values.addWidget(self.loadImpedanceLabel)
        values.addWidget(spacer)
        toolbar.addLayout(values,0)

        screenLayout = QVBoxLayout()

        self.supplyVoltage = QSlider(Qt.Horizontal)
        self.supplyVoltage.setFixedHeight(20)
        self.supplyVoltage.setMaximum(500)
        self.supplyVoltage.setMinimum(10)
        self.supplyVoltage.setValue(300)
        self.supplyVoltageChanged()
        screenLayout.addWidget(self.supplyVoltage)
        self.updateLoadLine()

        self.screenVoltage = QSlider(Qt.Horizontal)
        self.screenVoltage.setFixedHeight(20)
        self.screenVoltage.setMaximum(500)
        self.screenVoltage.setMinimum(10)
        self.screenVoltage.setValue(200)
        self.screenVoltageChanged()

        self.biasCurrent = QSlider(Qt.Horizontal)
        self.biasCurrent.setFixedHeight(20)
        self.biasCurrent.setMaximum(1000)
        self.biasCurrent.setMinimum(0)
        self.biasCurrent.setValue(480)
        self.biasCurrentChanged()

        screenLayout.addWidget(self.biasCurrent)
        screenLayout.addWidget(self.screenVoltage)

        self.loadImpedance = QSlider(Qt.Horizontal)
        self.loadImpedance.setFixedHeight(20)
        self.loadImpedance.setMaximum(500000)
        self.loadImpedance.setMinimum(10)
        self.loadImpedance.setValue(4200)
        self.loadImpedanceChanged()
        screenLayout.addWidget(self.loadImpedance)

        self.measureResult = QLabel()
        screenLayout.addWidget(self.measureResult)

        self.updateLoadLine()

        screenLayout.addWidget(QWidget())

        toolbar.addLayout(screenLayout,10)

        layout.addLayout(toolbar,0) # use stretch factor for force toolbar to not grow
        layout.addWidget(self.canvas,10)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.tubeChanged()
        self.updateResults()

        self.partnumber.currentIndexChanged.connect(self.tubeChanged)
        self.supplyVoltageLabel.returnPressed.connect(self.supplyVoltageLabelChanged)
        self.biasCurrentLabel.returnPressed.connect(self.biasCurrentLabelChanged)
        self.screenVoltageLabel.returnPressed.connect(self.screenVoltageLabelChanged)
        self.loadImpedanceLabel.returnPressed.connect(self.updateLoadLine)
        self.supplyVoltage.valueChanged.connect(self.supplyVoltageChanged)
        self.screenVoltage.valueChanged.connect(self.screenVoltageChanged)
        self.biasCurrent.valueChanged.connect(self.biasCurrentChanged)
        self.loadImpedance.valueChanged.connect(self.loadImpedanceChanged)

        self.running = True
        self.show()
        self.setFocus()

    def roundUp100(self,n):
        return (n + 99) // 100 * 100 

    def measureBegin(self,event):
        #print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
        self.voltage1 = event.xdata
        self.current1 = event.ydata

    def measureEnd(self,event):
        #print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
        self.voltage2 = event.xdata
        self.current2 = event.ydata

        dv = abs(self.voltage2-self.voltage1)
        di = abs(self.current2-self.current1)
        # print('deltaV:%0.1fV\ndeltaI:%0.4fA'%(dv,di))
        #print('power :%0.1fW'%((dv*di)/8))

        s = '\u0394V %0.1f-%0.1f=%0.1fV  \u0394A %d-%d=%0.1fmA  %0.1fW'%(self.voltage2,self.voltage1,dv,self.current1*1000,self.current2*1000,di*1000,(dv*di)/8)
        self.measureResult.setText(s)



    def keyPressEvent(self, event):
        k = event.text()

        if k == 'f':
            self.supplyVoltage.setValue(self.supplyVoltage.value()+1)
            self.supplyVoltageChanged()
        if k == 's':
            self.supplyVoltage.setValue(self.supplyVoltage.value()-1)
            self.supplyVoltageChanged()

        if k == 'l':
            self.screenVoltage.setValue(self.screenVoltage.value()+1)
            self.screenVoltageChanged()
        if k == 'j':
            self.screenVoltage.setValue(self.screenVoltage.value()-1)
            self.screenVoltageChanged()

        if k == 'i':
            self.biasCurrent.setValue(self.biasCurrent.value()+1)
            self.biasCurrentChanged()
        if k == 'k':
            self.biasCurrent.setValue(self.biasCurrent.value()-1)
            self.biasCurrentChanged()

        if k == 'q':
            self.onQuit()

    def onQuit(self):
        sys.exit()

    def supplyVoltageLabelChanged(self):
        self.supplyVoltage.setValue(int(self.supplyVoltageLabel.text()))
        self.updateLoadLine()

    def supplyVoltageChanged(self):
        self.supplyVoltageLabel.setText("%d"%self.supplyVoltage.value())
        self.xmax = self.roundUp100(2*int(self.supplyVoltage.value()))
        self.updatePlateDissipation()
        self.updateLoadLine()
        if self.running & (self.xmaxlast != self.xmax):
            self.updateResults()
            self.xmaxlast = self.xmax

    def screenVoltageLabelChanged(self):
        self.screenVoltage.setValue(int(self.screenVoltageLabel.text()))
        self.updateResults()

    def inductiveChanged(self):
        if self.inductive.isChecked() == True:
            self.lbiasi.setText("Iplate@Vplate")
        else:
            self.lbiasi.setText("Iplate")
        self.updateLoadLine()

    def screenVoltageChanged(self):
        self.screenVoltageLabel.setText("%d"%self.screenVoltage.value())
        # if self.running:
        #    self.autoscale.setChecked(False)
        self.updateResults()

    def biasCurrentLabelChanged(self):
        self.biasCurrent.setValue(int(10*float(self.biasCurrentLabel.text())))
        self.updateLoadLine()
        # self.updateResults()

    def biasCurrentChanged(self):
        self.biasCurrentLabel.setText("%0.1f"%(self.biasCurrent.value()/10))
        self.updateLoadLine()
        # self.updateResults()

    def loadImpedanceChanged(self):
        self.loadImpedanceLabel.setText("%d"%(self.loadImpedance.value()))
        self.updateLoadLine()

    def tubeChanged(self):
        name = self.partnumber.currentText()

        self.plateDissipationLabel.setText(self.tubes[name]['plateDissipation'])
        self.plateVoltagesMax = np.arange(30,self.xmax,5)
        self.plateCurrentsMax = float(self.plateDissipationLabel.text())/self.plateVoltagesMax

        self.supplyVoltage.setValue(int(self.tubes[name]['plateVoltage']))
        self.supplyVoltageLabel.setText("%d"%self.supplyVoltage.value())

        self.screenVoltage.setValue(int(self.tubes[name]['screenVoltage']))
        self.screenVoltageLabel.setText("%d"%self.screenVoltage.value())

        self.biasCurrent.setValue(int(10*float(self.tubes[name]['biasCurrent'])))
        self.biasCurrentLabel.setText("%0.1f"%(float(self.biasCurrent.value())/10))

        self.loadImpedanceLabel.setText(self.tubes[name]['load'])
        self.updateLoadLine()

        if self.running:
            self.autoscale.setChecked(True)

        self.updateResults()

    def updatePlateDissipation(self):
        self.plateVoltagesMax = np.arange(30,self.xmax,5)
        self.plateCurrentsMax = float(self.plateDissipationLabel.text())/self.plateVoltagesMax
        if self.running:
            self.update_plot()

    def updateLoadLine(self):
        self.loadlineVoltages = np.arange(0,self.xmax,5)
        self.biasi = float(self.biasCurrentLabel.text())/1000
        load = float(self.loadImpedanceLabel.text())
        vb = float(self.supplyVoltageLabel.text())

        m = -1/load
        if self.inductive.isChecked() == True:
            self.biasv = vb
            b = vb/load + self.biasi
            b2 = vb/(2*load) + self.biasi
            b5 = vb/(0.5*load) + self.biasi

            self.loadlineCurrents = m*self.loadlineVoltages + b
            self.loadlineCurrents2 = 2*m*self.loadlineVoltages + b5
            self.loadlineCurrents5 = 0.5*m*self.loadlineVoltages + b2

        else:
            self.biasv = vb - self.biasi * load
            b = vb/load
            self.loadlineCurrents = m*self.loadlineVoltages + b

            b2 = self.biasi - 2*m*self.biasv
            self.loadlineCurrents2 = 2*m*self.loadlineVoltages + b2 

            b5 = self.biasi - 0.5*m*self.biasv
            self.loadlineCurrents5 = 0.5*m*self.loadlineVoltages + b5

        if self.running:
            self.update_plot()


    def update_plot(self):
        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.grid(linestyle='--',linewidth=0.5,which='both')
        self.canvas.axes.minorticks_on()
        self.canvas.axes.set_xlim([0,self.xmax])

        for axis in ['top','bottom','left','right']:
            self.canvas.axes.spines[axis].set_linewidth(0.5)
        self.canvas.axes.tick_params(width=0.5)

        for i in range(30):
            self.canvas.axes.plot(self.xdata[i], self.ydata[i], 'black',linewidth=0.5)
            self.canvas.axes.plot(self.xdata[i], self.screencurrents[i], color='#FF8000',linewidth=0.5)

        if self.autoscale.isChecked() == True:
            self.canvas.axes.set_ylim(auto=True,bottom=0.0)
        else:
            self.canvas.axes.set_ylim(self.ylim)

        self.canvas.axes.autoscale(False)
        self.canvas.axes.plot(self.plateVoltagesMax,self.plateCurrentsMax, 'r',linewidth=2.0)
        self.canvas.axes.plot(self.loadlineVoltages,self.loadlineCurrents, 'g',linewidth=1.0)
        self.canvas.axes.plot(self.loadlineVoltages,self.loadlineCurrents2, 'm',linewidth=0.5)
        self.canvas.axes.plot(self.loadlineVoltages,self.loadlineCurrents5, 'c',linewidth=0.5)

        self.canvas.axes.plot(self.biasv,self.biasi, 'bo', markersize=4)

        self.canvas.draw()
        self.ylim = (0,self.canvas.axes.get_ylim()[1])

    def simulate(self):
        # print("simulate")
        subprocess.run(["/usr/bin/ngspice","-b","-r","plateChar.raw","-o","plateChar.out","plateChar.cir"],stdout=subprocess.DEVNULL)
        return rawread("plateChar.raw")

    def outputCircuitFile(self,pentode,gridVoltageRange,screenVoltage,supplyVoltage):
        f = open("plateChar.cir", "w")
        f.write(".title %s Plate Characteristics\n"%pentode)
        f.write(".include inc/%s.inc\n\n"%pentode)
        f.write("Vg g 0 -1\n")
        f.write("Vs s 0 %s\n"%screenVoltage)
        f.write("Vp p 0 100\n")
        f.write("Xtube p s g 0 %s\n\n"%pentode)
        f.write(".dc Vp 0 %s 5 Vg 0 %s -1\n"%("%d"%(2*int(supplyVoltage)+150),gridVoltageRange))
        f.write(".save v(g) v(g) v(s) v(p) i(Vs) i(Vp)\n")
        f.write(".end\n")
        f.close() 

    def updateResults(self):
        self.outputCircuitFile(self.partnumber.currentText(),-29,self.screenVoltage.value(),self.supplyVoltage.value())
        self.arrs,self.plots = self.simulate()

        x = [row[0] for row in self.arrs[0]] # list comprehension
        y = [-row[5] for row in self.arrs[0]]

        self.xdata = np.array_split(x,30) # list comprehension
        self.ydata = np.array_split(y,30)

        y = [-row[4] for row in self.arrs[0]]
        self.screencurrents = np.array_split(y,30)


        self.update_plot()
        self.setFocus()

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.setGeometry(750,500,2000,1500)
app.exec_()
