from __future__ import annotations

import json
import os
from pathlib import Path

import structlog

from app.config import settings
from app.models.report import Report

logger = structlog.get_logger()

REPORTS_DIR = Path("/tmp/w4agent/reports")


class ReportService:
    """Service for generating and exporting detection reports."""

    @staticmethod
    async def generate_report(task_id: str, db) -> Report:
        """Generate a report from task detection results."""
        from sqlalchemy import select, func
        from app.models.task import Task
        from app.models.issue import Issue, IssueSeverity
        from app.models.page import Page

        # Load task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()

        # Count issues by severity
        severity_counts = {}
        for severity in IssueSeverity:
            count_q = await db.execute(
                select(func.count(Issue.id))
                .where(Issue.task_id == task_id)
                .where(Issue.severity == severity)
            )
            severity_counts[severity.value] = count_q.scalar_one()

        total_issues = sum(severity_counts.values())

        # Count pages
        pages_q = await db.execute(
            select(func.count(Page.id)).where(Page.task_id == task_id)
        )
        total_pages = pages_q.scalar_one()

        # Calculate compliance score (simplified)
        if total_pages > 0:
            issues_per_page = total_issues / total_pages
            overall_score = max(0, 100 - (issues_per_page * 10))
        else:
            overall_score = 0

        # Build issue breakdown
        issue_breakdown = {
            "by_severity": severity_counts,
            "by_wcag_level": {},
        }

        report = Report(
            task_id=task_id,
            overall_score=round(overall_score, 1),
            level_a_score=round(overall_score * 1.1, 1),  # Simplified
            level_aa_score=round(overall_score, 1),
            level_aaa_score=round(overall_score * 0.9, 1),
            total_pages=total_pages,
            total_issues=total_issues,
            critical_issues=severity_counts.get("critical", 0),
            major_issues=severity_counts.get("major", 0),
            minor_issues=severity_counts.get("minor", 0),
            issue_breakdown=issue_breakdown,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report

    @staticmethod
    async def export_report(report: Report, format: str) -> str:
        """Export report in the specified format. Returns file path."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        if format == "json":
            return await ReportService._export_json(report)
        elif format == "html":
            return await ReportService._export_html(report)
        elif format == "pdf":
            return await ReportService._export_pdf(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    async def _export_json(report: Report) -> str:
        file_path = REPORTS_DIR / f"report_{report.task_id}.json"
        data = {
            "task_id": str(report.task_id),
            "overall_score": report.overall_score,
            "total_pages": report.total_pages,
            "total_issues": report.total_issues,
            "critical_issues": report.critical_issues,
            "major_issues": report.major_issues,
            "minor_issues": report.minor_issues,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "issue_breakdown": report.issue_breakdown,
        }
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return str(file_path)

    @staticmethod
    async def _export_html(report: Report) -> str:
        from jinja2 import Template

        template = Template(REPORT_HTML_TEMPLATE)
        html_content = template.render(report=report)

        file_path = REPORTS_DIR / f"report_{report.task_id}.html"
        file_path.write_text(html_content, encoding="utf-8")
        return str(file_path)

    @staticmethod
    async def _export_pdf(report: Report) -> str:
        # First generate HTML, then convert to PDF
        html_path = await ReportService._export_html(report)
        pdf_path = REPORTS_DIR / f"report_{report.task_id}.pdf"

        try:
            from weasyprint import HTML
            HTML(filename=html_path).write_pdf(str(pdf_path))
        except ImportError:
            logger.warning("weasyprint_not_installed", msg="Falling back to HTML")
            return html_path

        return str(pdf_path)


REPORT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>无障碍检测报告</title>
    <style>
        body { font-family: 'Microsoft YaHei', sans-serif; margin: 40px; color: #333; }
        .header { text-align: center; border-bottom: 2px solid #1890ff; padding-bottom: 20px; }
        .score { font-size: 48px; font-weight: bold; color: {% if report.overall_score >= 80 %}#52c41a{% elif report.overall_score >= 60 %}#faad14{% else %}#f5222d{% endif %}; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { flex: 1; padding: 15px; border: 1px solid #d9d9d9; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; }
        .critical { color: #f5222d; }
        .major { color: #fa8c16; }
        .minor { color: #faad14; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e8e8e8; }
        th { background: #fafafa; font-weight: bold; }
        .footer { text-align: center; color: #999; margin-top: 40px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Web无障碍检测报告</h1>
        <p>基于 WCAG 2.1 / GB/T 37668 标准</p>
        <div class="score">{{ report.overall_score }}分</div>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{{ report.total_pages }}</div>
            <div>检测页面</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ report.total_issues }}</div>
            <div>发现问题</div>
        </div>
        <div class="stat-card">
            <div class="stat-value critical">{{ report.critical_issues }}</div>
            <div>严重问题</div>
        </div>
        <div class="stat-card">
            <div class="stat-value major">{{ report.major_issues }}</div>
            <div>重要问题</div>
        </div>
    </div>

    {% if report.summary %}
    <h2>检测摘要</h2>
    <p>{{ report.summary }}</p>
    {% endif %}

    {% if report.recommendations %}
    <h2>改进建议</h2>
    <p>{{ report.recommendations }}</p>
    {% endif %}

    <div class="footer">
        <p>由 W4Agent 无障碍检测系统生成</p>
    </div>
</body>
</html>"""
