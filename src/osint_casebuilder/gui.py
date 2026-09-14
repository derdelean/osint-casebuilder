import sys
import os
import asyncio
import markdown

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QCheckBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextBrowser, QDialog, QSpinBox
)
from PyQt5.QtCore import Qt
from qasync import QEventLoop, asyncSlot

from utils.validation import validate_inputs
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
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.phone_region_input = QLineEdit()
        self.lookup_domain_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.location_input = QLineEdit()
        self.keywords_input = QLineEdit()
        self.domain_input = QLineEdit()
        self.top_sites_input = QSpinBox()
        self.top_sites_input.setRange(10, 5000)
        self.top_sites_input.setSingleStep(100)
        self.top_sites_input.setValue(500)
        self.all_sites_checkbox = QCheckBox("Alle Seiten (langsam)")
        self.pivot_depth_input = QSpinBox()
        self.pivot_depth_input.setRange(0, 3)
        self.infra_checkbox = QCheckBox("🛰️ Infra-/Breach-Intel")
        self.save_checkbox = QCheckBox("💾 Case speichern")
        self.save_checkbox.setChecked(True)
        self.generate_report_checkbox = QCheckBox("📝 Bericht generieren")

        self.phone_input.setPlaceholderText("+41441234567")
        self.phone_region_input.setPlaceholderText("CH (nur für nationale Nummern)")

        form_layout.addRow("🔤 Username:", self.username_input)
        form_layout.addRow("📧 Email:", self.email_input)
        form_layout.addRow("📞 Phone:", self.phone_input)
        form_layout.addRow("🗺️ Phone Region:", self.phone_region_input)
        form_layout.addRow("🧭 Domain Lookup:", self.lookup_domain_input)
        form_layout.addRow("👤 Fullname:", self.fullname_input)
        form_layout.addRow("📍 Location:", self.location_input)
        form_layout.addRow("🔎 Keywords:", self.keywords_input)
        form_layout.addRow("🌐 Target Domain:", self.domain_input)
        form_layout.addRow("🔢 Top Sites:", self.top_sites_input)
        form_layout.addRow("", self.all_sites_checkbox)
        form_layout.addRow("🔁 Pivot Depth:", self.pivot_depth_input)
        form_layout.addRow("", self.infra_checkbox)
        form_layout.addRow("", self.save_checkbox)
        form_layout.addRow("", self.generate_report_checkbox)

        self.search_button = QPushButton("🔍 Suche starten")
        self.search_button.clicked.connect(self.run_osint)

        self.view_report_button = QPushButton("📄 Markdown-Bericht anzeigen")
        self.view_report_button.clicked.connect(self.show_markdown_report)

        self.status_label = QLabel("Ready.")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Value", "Platform", "Score", "URL", "Evidence"])
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
        self.resize(900, 800)

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

        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        phone_region = self.phone_region_input.text().strip()
        lookup_domain = self.lookup_domain_input.text().strip()
        fullname = self.fullname_input.text()
        location = self.location_input.text()
        keywords = [k.strip() for k in self.keywords_input.text().split(",") if k.strip()]
        domain = self.domain_input.text()
        generate_report = self.generate_report_checkbox.isChecked()

        if not validate_inputs(username, fullname, location, keywords, domain, email, lookup_domain, phone):
            self.status_label.setText("⚠️ Bitte mindestens ein Feld ausfüllen.")
            spinner.close()
            self.search_button.setEnabled(True)
            return

        try:
            findings = await run_case(
                email=email or None,
                username=username or None,
                domain=lookup_domain or None,
                phone=phone or None,
                phone_region=phone_region or None,
                generate_report=generate_report,
                output_path=None,
                fullname=fullname or None,
                location=location or None,
                keywords=keywords or None,
                target_domain=domain or None,
                top_sites=100000 if self.all_sites_checkbox.isChecked() else self.top_sites_input.value(),
                pivot_depth=self.pivot_depth_input.value(),
                infra=self.infra_checkbox.isChecked(),
                save=self.save_checkbox.isChecked(),
            )

            print("🔍 DEBUG: First 3 findings:")
            for f in findings[:3]:
                print(f)

            # With sorting on, each setItem re-sorts mid-row and scatters cells.
            self.table.setSortingEnabled(False)
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
                evidence = "; ".join(item.get("evidence") or []) or (
                    "handle only" if item.get("type") == "username" else "-")
                self.table.setItem(row, 4, QTableWidgetItem(evidence))
            self.table.setSortingEnabled(True)

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
