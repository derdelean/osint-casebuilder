import sys
import os
import markdown
import asyncio
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QFormLayout, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QCheckBox, QLabel, QTextBrowser, QDialog
)
from qasync import QEventLoop, asyncSlot

from .controller import run_case


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
            browser.setText("❌ Report nicht gefunden.")

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

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)

        self.search_button = QPushButton("🔍 Suche starten")
        self.search_button.clicked.connect(self.run_osint)

        self.view_report_button = QPushButton("📄 Markdown-Bericht anzeigen")
        self.view_report_button.clicked.connect(self.show_markdown_report)

        layout.addLayout(form_layout)
        layout.addWidget(self.search_button)
        layout.addWidget(self.view_report_button)
        layout.addWidget(QLabel("📄 Ergebnisse:"))
        layout.addWidget(self.result_area)

        self.setLayout(layout)
        self.resize(600, 500)

    def show_markdown_report(self):
        report_dir = os.path.abspath("reports")
        files = sorted([f for f in os.listdir(report_dir) if f.endswith(".md")], reverse=True)
        if files:
            latest_report = os.path.join(report_dir, files[0])
            viewer = MarkdownViewer(latest_report)
            viewer.exec_()
        else:
            self.result_area.append("⚠️ Kein Markdown-Report gefunden.")

    @asyncSlot()
    async def run_osint(self):
        self.result_area.clear()
        username = self.username_input.text()
        fullname = self.fullname_input.text()
        location = self.location_input.text()
        keywords = self.keywords_input.text()
        domain = self.domain_input.text()
        generate_report = self.generate_report_checkbox.isChecked()

        findings = await run_case(
            email=None,
            username=username or None,
            domain=domain or None,
            generate_report=generate_report,
            output_path=None,
        )

        if findings:
            self.result_area.append(f"✅ {len(findings)} Fundstellen gefunden:\n")
            for item in findings:
                self.result_area.append(f"- {item.get('value')} → {item.get('source')}")
                if "score" in item:
                    score = item["score"]
                    if score >= 0.85:
                        level = "hoch ✅"
                    elif score >= 0.5:
                        level = "mittel ⚠️"
                    else:
                        level = "niedrig ❌"
                    self.result_area.append(f"  Score: {score} ({level})")
                self.result_area.append("")
        else:
            self.result_area.append("❌ Keine Fundstellen.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    gui = OSINTGui()
    gui.show()

    with loop:
        loop.run_forever()
