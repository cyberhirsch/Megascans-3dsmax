import os, json, sys, socket, time, re

_path_ = os.path.dirname(__file__).replace("\\", "/")
if _path_ not in sys.path:
    sys.path.append(_path_)

import MS_Importer
from Logging import Logger
_importerSetup_ = MS_Importer.LiveLinkImporter()

MSLIVELINK_VERSION = "5.5"

# Updated import statements for PySide6
try:
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
except ImportError:
    print("PySide6 is not available.")

"""
#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*
#####################################################################################
MegascansLiveLinkAPI is the core component of the Megascans Plugin plugins.
This API relies on a QThread to monitor any incoming data from Bridge by communicating
via a socket port.

This module has a bunch of classes and functions that are standardized as much as possible
to make sure you don't have to modify them too much for them to work in any python-compatible
software.
If you're looking into extending the user interface then you can modify the MegascansLiveLinkUI
class to suit your needs.
#####################################################################################
#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*"""

def GetHostApp():
    try:
        mainWindow = QApplication.activeWindow()
        while True:
            lastWin = mainWindow.parent()
            if lastWin:
                mainWindow = lastWin
            else:
                break
        return mainWindow
    except:
        pass

class QLiveLinkMonitor(QThread):

    Bridge_Call = Signal()
    Instance = []

    def __init__(self):
        QThread.__init__(self)
        self.TotalData = b""
        QLiveLinkMonitor.Instance.append(self)

    def __del__(self):
        self.quit()
        self.wait()

    def stop(self):
        self.terminate()

    def run(self):
        time.sleep(0.025)
        try:
            host, port = 'localhost', 13292
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_.bind((host, port))

            while True:
                socket_.listen(5)
                client, address = socket_.accept()
                data = ""
                data = client.recv(4096*2)

                if data != "":
                    self.TotalData = b""
                    self.TotalData += data
                    while True:
                        data = client.recv(4096*2)
                        if data:
                            self.TotalData += data
                        else:
                            break

                    time.sleep(0.05)
                    self.Bridge_Call.emit()
                    time.sleep(0.05)
        except:
            pass

    def InitializeImporter(self):
        import pymxs
        json_array = json.loads(self.TotalData)
        for asset_ in json_array:
            self = _importerSetup_.Identifier
            self.set_Asset_Data(asset_)
            try:
                guid = asset_['guid']
                assetID = asset_['id']
            except:
                guid = ""
                assetID = ""

            if len(json_array) > 1:
                bridge_event = "BRIDGE_BULK_EXPORT_ASSET"
            else:
                bridge_event = "BRIDGE_EXPORT_ASSET"

            try:
                Logger(pymxs.runtime.execute("classof renderers.current"), pymxs.runtime.maxversion()[7], guid, assetID, bridge_event)
            except:
                Logger(pymxs.runtime.execute("classof renderers.current"), "2019 or lower", guid, assetID, bridge_event)

stylesheet_ = ("""
QCheckBox { background: transparent; color: #E6E6E6; font-family: Source Sans Pro; font-size: 14px; }
QCheckBox::indicator:hover { border: 2px solid #2B98F0; background-color: transparent; }
QCheckBox::indicator:checked:hover { background-color: #2B98F0; border: 2px solid #73a5ce; }
QCheckBox::indicator{ color: #67696a; background-color: transparent; border: 2px solid #67696a;
width: 14px; height: 14px; border-radius: 2px; }
QCheckBox::indicator:checked { border: 2px solid #18191b;
background-color: #2B98F0; color: #ffffff; }
QCheckBox::hover { spacing: 12px; background: transparent; color: #ffffff; }
QCheckBox::checked { color: #ffffff; }
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { border: 1px solid #444; }
QCheckBox::disabled { background: transparent; color: #414141; font-family: Source Sans Pro;
font-size: 14px; margin: 0px; text-align: center; }

QComboBox { color: #FFFFFF; font-size: 14px; font-family: Source Sans Pro;
selection-background-color: #1d1e1f; background-color: #1d1e1f; }
QComboBox:hover { color: #c9c9c9; font-size: 14px; font-family: Source Sans Pro;
selection-background-color: #232426; background-color: #232426; }
""")

class LiveLinkUI(QWidget):

    Instance = []
    Settings = [0, 0, 0]

    def __init__(self, _importerSetup_, parent=GetHostApp()):
        super(LiveLinkUI, self).__init__(parent)

        LiveLinkUI.Instance = self
        self.Importer = _importerSetup_

        self._path_ = _path_
        self.setObjectName("LiveLinkUI")
        img_ = QPixmap(os.path.join(self._path_, "MS_Logo.png"))
        self.setWindowIcon(QIcon(img_))
        self.setMinimumWidth(250)
        self.setWindowTitle("MS Plugin " + MSLIVELINK_VERSION + " - 3ds Max")
        self.setWindowFlags(Qt.Window)

        self.style_ = ("""  QWidget#LiveLinkUI { background-color: #262729; } """)
        self.setStyleSheet(self.style_)

        self.MainLayout = QVBoxLayout()
        self.setLayout(self.MainLayout)
        self.MainLayout.setSpacing(5)
        self.MainLayout.setContentsMargins(5, 2, 5, 2)

        self.checks_l = QVBoxLayout()
        self.checks_l.setSpacing(2)
        self.MainLayout.addLayout(self.checks_l)

        self.applytoSel = QCheckBox("Apply Material to Selection")
        self.applytoSel.setToolTip("Applies the imported material(s) to your selection.")
        self.applytoSel.setChecked(self.Importer.getPref("Material_to_Sel"))
        self.applytoSel.setFixedHeight(30)
        self.applytoSel.setStyleSheet(stylesheet_)
        self.checks_l.addWidget(self.applytoSel)

        self.enableDisplacement = QCheckBox("Import 3D Assets with Displacement")
        self.enableDisplacement.setToolTip("Enables displacement for 3D Assets")
        self.enableDisplacement.setChecked(self.Importer.getPref("Enable_Displacement"))
        self.enableDisplacement.setFixedHeight(30)
        self.enableDisplacement.setStyleSheet(stylesheet_)
        self.checks_l.addWidget(self.enableDisplacement)

        self.applytoSel.stateChanged.connect(self.settingsChanged)
        self.enableDisplacement.stateChanged.connect(self.settingsChanged)

    def settingsChanged(self):
        settings_data = self.Importer.loadSettings()
        settings_data["Material_to_Sel"] = self.applytoSel.isChecked()
        settings_data["Enable_Displacement"] = self.enableDisplacement.isChecked()
        self.Importer.updateSettings(settings_data)

def initLiveLink():
    if LiveLinkUI.Instance != None:
        try:
            LiveLinkUI.Instance.close()
        except:
            pass

    LiveLinkUI.Instance = LiveLinkUI(_importerSetup_)
    LiveLinkUI.Instance.show()
    pref_geo = QRect(500, 300, 460, 30)
    LiveLinkUI.Instance.setGeometry(pref_geo)
    return LiveLinkUI.Instance

def createToolbarMenuPymxs():
    import pymxs
    pymxs.runtime.execute(" global mxsInit = 0 ")
    pymxs.runtime.mxsInit = initLiveLink
    pymxs.runtime.execute("""
-- Sample menu extension script
-- If this script is placed in the "stdplugs\\stdscripts"
-- folder, then this will add the new items to MAX's menu bar
-- when MAX starts.
-- A sample macroScript that we will attach to a menu item
macroScript Megascans
category: "Quixel"
tooltip: "MS Plugin"
(
on execute do mxsInit()
)


-- This example adds a new sub-menu to MAX's main menu bar.
-- It adds the menu just before the "Help" menu.
if ((menuMan.findMenu "Megascans") == undefined) then
--if menuMan.registerMenuContext 0x1ee76d8f then
(
-- Get the main menu bar
local mainMenuBar = menuMan.getMainMenuBar()
-- Create a new menu
local subMenu = menuMan.createMenu "Megascans"
-- create a menu item that calls the sample macroScript
local subItem = menuMan.createActionItem "Megascans" "Quixel"
-- Add the item to the menu
subMenu.addItem subItem -1
-- Create a new menu item with the menu as it's sub-menu
local subMenuItem = menuMan.createSubMenuItem "Megascans" subMenu
-- compute the index of the next-to-last menu item in the main menu bar
local subMenuIndex = mainMenuBar.numItems() - 1
-- Add the sub-menu just at the second to last slot
mainMenuBar.addItem subMenuItem subMenuIndex
-- redraw the menu bar with the new item
menuMan.updateMenuBar()
)
"""
    )

def StartSocketServer():
    try:
        if len(QLiveLinkMonitor.Instance) == 0:
            bridge_monitor = QLiveLinkMonitor()
            bridge_monitor.Bridge_Call.connect(bridge_monitor.InitializeImporter)
            bridge_monitor.start()
        print("Quixel Bridge Plugin v" + MSLIVELINK_VERSION + " started successfully.")
    except:
        print("Quixel Bridge Plugin v" + MSLIVELINK_VERSION + " failed to start.")
        pass

if __name__ == "builtins" or __name__ == "__builtin__":
    try:
        createToolbarMenuPymxs()
    except:
        print("Failed to create menu.")
    StartSocketServer()
