from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from datetime import date


def change_class(val: str) -> str:
    v = val.strip().lower()
    if not v:
        return "change-flat"
    if v.startswith(("+", "↑")):
        return "change-pos"
    if v.startswith(("-", "↓")):
        return "change-neg"
    return "change-flat"


@dataclass
class InvertedHoldingsLog:
    """
    Collect daily holdings and write an HTML table with:

      rows    = dates (newest first)
      columns = Date | Change | assets | Notes
      cells   = percent of equity (blank if < min_pct_to_show)

    Sticky headers + first column.
    """
    file_path: str
    min_pct_to_show: float = 2.0

    columns: list[str] = field(default_factory=list)
    rows: list[tuple[str, list[str], str, str, str]] = field(
        default_factory=list
    )  # (date, asset_cells, value_cell, change_cell, notes_cell)

    _has_notes_column: bool = False
    _has_change_column: bool = False
    _has_value_column: bool = False

    def clear(self) -> None:
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

        self.columns.clear()
        self.rows.clear()
        self._last_logged_date = None
        self._has_notes_column = False
        self._has_change_column = False

    def collect(
            self,
            strategy,
            assets,
            change: str | None = None,
            value: str | None = None,
            notes: str | None = None,
    ) -> None:
        dt = strategy.datas[0].datetime.date(0)
        if self._last_logged_date == dt:
            return
        self._last_logged_date = dt

        equity = float(strategy.broker.getvalue())
        if equity <= 0:
            return

        if change is not None:
            self._has_change_column = True
        change_cell = "" if change is None else str(change)

        if value is not None:
            self._has_value_column = True
        value_cell = "" if value is None else str(value)

        if notes is not None:
            self._has_notes_column = True
        notes_cell = "" if notes is None else str(notes)

        day_columns: list[str] = []
        day_pct: dict[str, float] = {}

        for item in assets:
            name, pct = self._holdings_pct(strategy, item, equity)
            day_columns.append(name)
            day_pct[name] = pct

        if not self.columns:
            self.columns = day_columns

        if day_columns != self.columns:
            raise ValueError(
                "InvertedHoldingsLog column mismatch. "
                "Pass the same assets list (same order) every day. "
                f"Expected={self.columns}, Got={day_columns}"
            )

        row_cells: list[str] = []
        for c in self.columns:
            pct = float(day_pct.get(c, 0.0))
            if abs(pct) < float(self.min_pct_to_show):
                row_cells.append("")
            else:
                row_cells.append(f"{pct:.1f}%")

        self.rows.insert(
            0,
            (
                dt.isoformat(),
                row_cells,
                value_cell,
                change_cell,
                notes_cell,
            ),
        )

    def _get_css(self) -> str:
            """Return CSS styling for both chart and table."""
            return """
        :root { color-scheme: light dark; }
        body { 
            font-size:12px; 
            font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; 
            margin: 4px; 
        }
        .chart-container { 
            height: 500px; 
            margin-bottom: 20px; 
            border: 1px solid #bbb; 
            border-radius: 8px; 
            padding: 10px; 
            background: Canvas;
        }
        .table-container { 
            height: 100vh; 
            overflow-y: auto; 
            border: 1px solid #bbb; 
            border-radius: 8px; 
        }
        table { border-collapse: collapse; width: max-content; min-width: 100%; }
        th, td { border: 1px solid #bbb; padding: 3px 5px; white-space: nowrap; text-align: right; }
        th { position: sticky; top: 0; z-index: 2; background: Canvas; }
        th:first-child, td:first-child {
            position: sticky; left: 0; z-index: 3;
            background: Canvas; text-align: left;
        }
        tbody tr:nth-child(even) td {
            background: color-mix(in srgb, Canvas 92%, CanvasText 8%);
        }
        th.notes, td.notes { text-align: left; }
        td.change-pos { color: #1a7f37; font-weight: 600; }
        td.change-neg { color: #c93c37; font-weight: 600; }
        td.change-flat { color: #777; }
        """

    def _get_column_headers(self) -> list[str]:
            """Get ordered list of column headers."""
            return (
                ["Date"]
                + self.columns
                + (["Value"] if self._has_value_column else [])
                + (["Change"] if self._has_change_column else [])
                + (["Notes"] if self._has_notes_column else [])
            )

    def _parse_percentage(self, pct_str: str) -> float:
        """Parse percentage string like '+8,062.2%' to float 8062.2"""
        if not pct_str or pct_str.strip() == "":
            return 0.0
        cleaned = pct_str.replace("%", "").replace("+", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _format_date(self, iso_yyyy_mm_dd: str) -> str:
        """Format ISO date to display format."""
        d = date.fromisoformat(iso_yyyy_mm_dd)
        return f"{d:%b} {d.day}, {d:%Y}"

    def _escape_html(self, s: str) -> str:
        """Escape HTML special characters."""
        return (
                str(s)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

    def generate_chart_data(self) -> tuple[list[str], list[float]]:
            """Extract chart data from rows and return labels and values."""
            chart_data = []
            for date_str, cells, value_cell, change_cell, notes_cell in reversed(self.rows):
                chart_data.append({
                    'date': self._format_date(date_str),
                    'change': self._parse_percentage(value_cell)  # Use value_cell for cumulative values
                })

            chart_labels = [item['date'] for item in chart_data]
            chart_values = [item['change'] for item in chart_data]
            return chart_labels, chart_values

    def generate_chart_html(self, chart_labels: list[str], chart_values: list[float]) -> str:
            """Generate HTML for Chart.js line chart."""
            return f'''
            <div class="chart-container">
                <canvas id="portfolioChart"></canvas>
                <button onclick="resetZoom()" style="position: absolute; top: 10px; right: 10px; 
                       background: #1a7f37; color: white; border: none; 
                       padding: 5px 10px; border-radius: 3px; 
                       cursor: pointer; font-size: 12px; z-index: 10;">
                    Reset Zoom
                </button>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.0/dist/chartjs-plugin-zoom.min.js"></script>

        <script>
            const ctx = document.getElementById('portfolioChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {chart_labels},
                    datasets: [{{
                        label: 'Portfolio Performance (%)',
                        data: {chart_values},
                        borderColor: '#1a7f37',
                        backgroundColor: 'rgba(26, 127, 55, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }},
                        tooltip: {{
                            mode: 'index',
                            intersect: false,
                            callbacks: {{
                                label: function(context) {{
                                    return 'Performance: ' + context.parsed.y.toFixed(1) + '%';
                                }}
                            }}
                        }},
                        zoom: {{
                            limits: {{
                                x: {{min: 'original', max: 'original'}},
                                y: {{min: 'original', max: 'original'}}
                            }},
                            zoom: {{
                                wheel: {{
                                    enabled: true,
                                    speed: 0.5
                                }},
                                pinch: {{
                                    enabled: false
                                }},
                                drag: {{
                                    enabled: false
                                }}
                            }},
                            pan: {{
                                enabled: true,
                                mode: 'xy',
                                scaleMode: 'xy'
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: false,
                            title: {{
                                display: true,
                                text: 'Cumulative Performance (%)'
                            }},
                            ticks: {{
                                callback: function(value) {{
                                    return value.toFixed(0) + '%';
                                }}
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Date'
                            }}
                        }}
                    }}
                }}
            }});
            
            function resetZoom() {{
                const chart = Chart.getChart('portfolioChart');
                if (chart) {{
                    chart.resetZoom();
                }}
            }}
        </script>
            '''

    def generate_table_html(self) -> str:
            """Generate HTML table with all holdings data."""
            cols = self._get_column_headers()
            html_parts = ['<div class="table-container"><table><thead><tr>']

            # Headers
            for c in cols:
                cls = " class='notes'" if c == "Notes" else ""
                html_parts.append(f"<th{cls}>{self._escape_html(c)}</th>")

            html_parts.append("</tr></thead><tbody>")

            # Data rows
            for date_str, cells, value_cell, change_cell, notes_cell in self.rows:
                html_parts.append("<tr>")
                html_parts.append(f"<td>{self._escape_html(self._format_date(date_str))}</td>")

                for cell in cells:
                    html_parts.append(f"<td>{self._escape_html(cell)}</td>")

                if self._has_change_column:
                    cls = change_class(change_cell)
                    html_parts.append(f"<td class='{cls}'>{self._escape_html(change_cell)}</td>")

                if self._has_value_column:
                    html_parts.append(f"<td>{self._escape_html(value_cell)}</td>")

                if self._has_notes_column:
                    html_parts.append(f"<td class='notes'>{self._escape_html(notes_cell)}</td>")

                html_parts.append("</tr>")

            html_parts.append("</tbody></table></div>")
            return ''.join(html_parts)

    def write(self) -> None:
        """Generate HTML with both chart and table sections."""
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Generate chart data and HTML
        chart_labels, chart_values = self.generate_chart_data()
        chart_html = self.generate_chart_html(chart_labels, chart_values)
        table_html = self.generate_table_html()

        # Build final HTML
        html = [
            "<!doctype html><html><head><meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"<style>{self._get_css()}</style>",
            "</head><body>",
            chart_html,
            table_html,
            "</body></html>"
        ]

        path.write_text("".join(html), encoding="utf-8")

    @staticmethod
    def _holdings_pct(strategy, item, equity: float) -> tuple[str, float]:
        if isinstance(item, str) and item.upper() == "CASH":
            return "CASH", (float(strategy.broker.getcash()) / equity) * 100.0

        data = item
        if isinstance(data, str):
            return data, 0.0  # String items (like "CASH") have no position value
        
        name = (getattr(data, "_name", None) or "UNKNOWN").replace("_1H", "")
        pos = strategy.getposition(data)
        value = abs(pos.size) * float(data.close[0]) if pos.size else 0.0
        return name, (value / equity) * 100.0
