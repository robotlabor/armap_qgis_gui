import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject

class TableWidget(QWidget):
    # Signal létrehozása, amely a törölt sorokat továbbítja
    row_deleted = pyqtSignal(list)
    coords_sent = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Táblázat kezelő")

        # Fő elrendezés
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Táblázat létrehozása
        self.table = QTableWidget(0, 5)  # 5 sor, 3 oszlop
        self.table.setHorizontalHeaderLabels(["FID","UTMX", "UTMY", "WGS84LON", "WGS84LAT"])
        main_layout.addWidget(self.table)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Gombok vízszintes elrendezése
        button_layout = QHBoxLayout()

        # Sor törlése gomb
        self.delete_button = QPushButton("Kiválasztottak törlése")
        self.delete_button.clicked.connect(self.delete_selected_rows)
        button_layout.addWidget(self.delete_button)

        # Táblázat adatok exportálása JSON-ként
        self.export_button = QPushButton("Küldés")
        self.export_button.clicked.connect(self.export_to_json)
        button_layout.addWidget(self.export_button)

        # Új sor hozzáadása gomb
        #self.add_row_button = QPushButton("Új sor hozzáadása")
        #self.add_row_button.clicked.connect(self.add_new_row)
        #button_layout.addWidget(self.add_row_button)

        # Gombok hozzáadása a fő elrendezéshez
        main_layout.addLayout(button_layout)

    def delete_selected_rows(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        
        # Az oszlop, amelynek értékeit menteni szeretnénk (pl. az első oszlop)
        target_column = 0
        deleted_FIDs = []  # Lista a kiválasztott sorok adott oszlopértékeihez

        for row in sorted(selected_rows, reverse=True):
            item = self.table.item(row, target_column)
            if item:  # Ha az adott cella nem üres
                deleted_FIDs.append(int(item.text()))
            self.table.removeRow(row)

        # Jelet küldünk a törölt sorok azonosítóival
        self.row_deleted.emit(deleted_FIDs)

        QMessageBox.information(self, "Törlés", "Kiválasztott sorok törölve!")

    def export_to_json(self):
        table_data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                row_data[self.table.horizontalHeaderItem(column).text()] = item.text() if item else ""
            table_data.append(row_data)
        #json_data = json.dumps(table_data, ensure_ascii=False, indent=4)
        json_data = json.dumps(table_data)
        
        # Jelet küldünk a törölt sorok azonosítóival
        #self.coords_sent.emit(table_data)
        self.coords_sent.emit(json_data)

        QMessageBox.information(self, "JSON Export", f"Táblázat adatai JSON formátumban:\n{json_data}")

    def add_new_row(self, values):
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)
        
        # Cellák értékeinek beállítása a megadott értékek alapján
        for column, value in enumerate(values):
            if column < self.table.columnCount():
                self.table.setItem(current_row_count, column, QTableWidgetItem(value))
        #QMessageBox.information(self, "Új sor", "Új sor hozzáadva!")

# Alkalmazás futtatása
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TableWidget()
    window.show()
    sys.exit(app.exec_())