import sys
import os
import asyncio
import markdown

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QCheckBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextBrowser, QDialog
)
from PyQt5.QtCore import Qt
from qasync import QEventLoop, asyncSlot

from .controller import run_case
from .components.loading_spinner import LoadingSpinner


class MarkdownViewer(QDialog):
    def __init__(self, md_path):
        super().__init__()
        self.setWindowTitle("📄 Markdown-Bericht")
        layout = QVBoxLayout()
        browser = QTextBrowser()

        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
                html = markdown.markdown(md_content, extensions=["extra", "tables"])
                browser.setHtml(html)
        else:
            browser.setText("❌ Report not found.")

        layout.addWidget(browser)
        self.setLayout(layout)
        self.resize(700, 500)


class OSINTGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSINT CaseBuilder")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.location_input = QLineEdit()
        self.keywords_input = QLineEdit()
        self.domain_input = QLineEdit()
        self.generate_report_checkbox = QCheckBox("📝 Bericht generieren")

        form_layout.addRow("🔤 Username:", self.username_input)
        form_layout.addRow("👤 Fullname:", self.fullname_input)
        form_layout.addRow("📍 Location:", self.location_input)
        form_layout.addRow("🔎 Keywords:", self.keywords_input)
        form_layout.addRow("🌐 Target Domain:", self.domain_input)
        form_layout.addRow("", self.generate_report_checkbox)

        self.search_button = QPushButton("🔍 Suche starten")
        self.search_button.clicked.connect(self.run_osint)

        self.view_report_button = QPushButton("📄 Markdown-Bericht anzeigen")
        self.view_report_button.clicked.connect(self.show_markdown_report)

        self.status_label = QLabel("Ready.")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Username", "Platform", "Score", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)

        layout.addLayout(form_layout)
        layout.addWidget(self.search_button)
        layout.addWidget(self.view_report_button)
        layout.addWidget(QLabel("📊 Results:"))
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.resize(800, 600)

    def show_markdown_report(self):
        report_dir = os.path.abspath("reports")
        files = sorted([f for f in os.listdir(report_dir) if f.endswith(".md")], reverse=True)
        if files:
            latest_report = os.path.join(report_dir, files[0])
            viewer = MarkdownViewer(latest_report)
            viewer.exec_()
        else:
            self.status_label.setText("⚠️ Kein Markdown-Report gefunden.")

    @asyncSlot()
    async def run_osint(self):
        self.search_button.setEnabled(False)
        self.status_label.setText("⏳ Searching...")
        self.table.setRowCount(0)

        spinner = LoadingSpinner()
        spinner.show()

        username = self.username_input.text()
        fullname = self.fullname_input.text()
        location = self.location_input.text()
        keywords = self.keywords_input.text()
        domain = self.domain_input.text()
        generate_report = self.generate_report_checkbox.isChecked()

        try:
            findings = await run_case(
                email=None,
                username=username or None,
                domain=domain or None,
                generate_report=generate_report,
                output_path=None,
                fullname=fullname or None,
                location=location or None,
                keywords=keywords or None,
                target_domain=domain or None,
            )

            print("🔍 DEBUG: First 3 findings:")
            for f in findings[:3]:
                print(f)

            for item in findings:
                user = item.get("value", "")
                source = item.get("source", "")
                platform = self.extract_platform(source)
                score = item.get("score")
                score_str = f"{score:.2f}" if isinstance(score, (float, int)) else "-"

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(user or "-"))
                self.table.setItem(row, 1, QTableWidgetItem(platform or "-"))
                self.table.setItem(row, 2, QTableWidgetItem(score_str))
                self.table.setItem(row, 3, QTableWidgetItem(source or "-"))

            self.status_label.setText(f"✅ {len(findings)} Found findings.")
        except Exception as e:
            self.status_label.setText(f"❌ Fehler: {str(e)}")
        finally:
            spinner.close()
            self.search_button.setEnabled(True)

    def extract_platform(self, url: str) -> str:
        try:
            return url.split("//")[1].split("/")[0]
        except Exception:
            return "Unbekannt"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    gui = OSINTGui()
    gui.show()
    with loop:
        loop.run_forever()
