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
    async def generate_report(
        task_id: str, db, report_data: dict | None = None
    ) -> Report:
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

        # Calculate compliance score using severity-weighted formula
        # Weights: critical=10, major=5, minor=2, info=0
        critical = severity_counts.get("critical", 0)
        major = severity_counts.get("major", 0)
        minor = severity_counts.get("minor", 0)
        if total_pages > 0:
            weighted_deduction = (critical * 10 + major * 5 + minor * 2) / total_pages
            overall_score = max(0, 100 - weighted_deduction)
        else:
            overall_score = 0

        # Build issue breakdown
        issue_breakdown = {
            "by_severity": severity_counts,
            "by_wcag_level": {},
        }

        # Use LLM-generated summary/recommendations from orchestrator if available
        summary = None
        recommendations = None
        if report_data:
            summary = report_data.get("summary")
            recommendations = report_data.get("recommendations")
            if isinstance(recommendations, list):
                recommendations = "\n".join(f"- {r}" for r in recommendations)

        report = Report(
            task_id=task_id,
            overall_score=round(overall_score, 1),
            level_a_score=min(100, round(overall_score * 1.1, 1)),
            level_aa_score=round(overall_score, 1),
            level_aaa_score=round(overall_score * 0.9, 1),
            total_pages=total_pages,
            total_issues=total_issues,
            critical_issues=critical,
            major_issues=major,
            minor_issues=minor,
            summary=summary,
            recommendations=recommendations,
            issue_breakdown=issue_breakdown,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report

    @staticmethod
    async def _load_issues_for_export(task_id: str) -> list[dict]:
        """Load all issues with page URLs for export."""
        from sqlalchemy import select
        from app.db.session import async_session_factory
        from app.models.issue import Issue
        from app.models.page import Page

        async with async_session_factory() as db:
            result = await db.execute(
                select(Issue).where(Issue.task_id == task_id).order_by(Issue.created_at)
            )
            items = result.scalars().all()

            # Collect page URLs
            page_ids = {item.page_id for item in items}
            page_url_map: dict = {}
            if page_ids:
                page_result = await db.execute(
                    select(Page.id, Page.url).where(Page.id.in_(page_ids))
                )
                page_url_map = {row.id: row.url for row in page_result.all()}

            return [
                {
                    "severity": item.severity.value if hasattr(item.severity, 'value') else item.severity,
                    "wcag_criterion": item.wcag_criterion,
                    "wcag_level": item.wcag_level.value if hasattr(item.wcag_level, 'value') else item.wcag_level,
                    "title": item.title,
                    "description": item.description,
                    "recommendation": item.recommendation or "",
                    "detected_by": item.detected_by,
                    "page_url": page_url_map.get(item.page_id, ""),
                }
                for item in items
            ]

    @staticmethod
    async def export_report(report: Report, format: str) -> str:
        """Export report in the specified format. Returns file path."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        issues = await ReportService._load_issues_for_export(str(report.task_id))

        if format == "json":
            return await ReportService._export_json(report, issues)
        elif format == "html":
            return await ReportService._export_html(report, issues)
        elif format == "pdf":
            return await ReportService._export_pdf(report, issues)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    async def _export_json(report: Report, issues: list[dict]) -> str:
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
            "issues": issues,
        }
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return str(file_path)

    @staticmethod
    async def _export_html(report: Report, issues: list[dict]) -> str:
        from jinja2 import Template

        template = Template(REPORT_HTML_TEMPLATE)
        html_content = template.render(report=report, issues=issues)

        file_path = REPORTS_DIR / f"report_{report.task_id}.html"
        file_path.write_text(html_content, encoding="utf-8")
        return str(file_path)

    @staticmethod
    async def _export_pdf(report: Report, issues: list[dict]) -> str:
        # First generate HTML, then convert to PDF
        html_path = await ReportService._export_html(report, issues)
        pdf_path = REPORTS_DIR / f"report_{report.task_id}.pdf"

        try:
            from weasyprint import HTML
            HTML(filename=html_path).write_pdf(str(pdf_path))
        except (ImportError, OSError) as e:
            logger.warning("weasyprint_unavailable", msg=f"Falling back to HTML: {e}")
            return html_path

        return str(pdf_path)


REPORT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>无障碍检测报告</title>
    <style>
        @page { size: A4 landscape; margin: 15mm; }
        body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 0; color: #333; font-size: 9px; line-height: 1.4; }
        h1 { font-size: 18px; margin: 0 0 4px 0; }
        h2 { font-size: 12px; margin: 0; }
        p { margin: 4px 0; font-size: 9px; }
        .header { text-align: center; border-bottom: 2px solid #1890ff; padding-bottom: 10px; margin-bottom: 10px; }
        .header p { color: #666; }
        .score { font-size: 32px; font-weight: bold; margin: 6px 0; color: {% if report.overall_score >= 80 %}#52c41a{% elif report.overall_score >= 60 %}#faad14{% else %}#f5222d{% endif %}; }
        .stats { display: flex; gap: 10px; margin: 10px 0; }
        .stat-card { flex: 1; padding: 8px; border: 1px solid #d9d9d9; border-radius: 6px; text-align: center; }
        .stat-value { font-size: 18px; font-weight: bold; }
        .stat-card div:last-child { font-size: 8px; color: #666; margin-top: 2px; }
        .critical { color: #f5222d; }
        .major { color: #fa8c16; }
        .minor { color: #faad14; }
        .section-title { font-size: 11px; margin-top: 14px; padding-bottom: 4px; border-bottom: 1px solid #d9d9d9; }
        table { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 8px; }
        th, td { padding: 4px 5px; text-align: left; border: 1px solid #ddd; word-break: break-all; }
        th { background: #f5f5f5; font-weight: bold; font-size: 8px; }
        tr:nth-child(even) { background: #fafafa; }
        .severity-critical { background: #fff1f0; color: #cf1322; font-weight: bold; }
        .severity-major { background: #fff7e6; color: #d46b08; font-weight: bold; }
        .severity-minor { background: #fffbe6; color: #d4b106; }
        .severity-info { background: #e6f7ff; color: #096dd9; }
        .page-url { color: #1890ff; font-size: 7px; }
        .footer { text-align: center; color: #999; margin-top: 16px; font-size: 8px; }
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
    <h2 class="section-title">检测摘要</h2>
    <p>{{ report.summary }}</p>
    {% endif %}

    {% if report.recommendations %}
    <h2 class="section-title">改进建议</h2>
    <p>{{ report.recommendations }}</p>
    {% endif %}

    <h2 class="section-title">问题详情 ({{ issues|length }})</h2>
    {% if issues %}
    <table>
        <thead>
            <tr>
                <th style="width:45px">严重程度</th>
                <th style="width:55px">WCAG准则</th>
                <th style="width:30px">级别</th>
                <th style="width:120px">问题标题</th>
                <th>描述</th>
                <th style="width:100px">页面网址</th>
                <th>建议</th>
                <th style="width:35px">来源</th>
            </tr>
        </thead>
        <tbody>
            {% for issue in issues %}
            <tr>
                <td class="severity-{{ issue.severity }}">
                    {% if issue.severity == 'critical' %}严重{% elif issue.severity == 'major' %}重要{% elif issue.severity == 'minor' %}一般{% else %}提示{% endif %}
                </td>
                <td>{{ issue.wcag_criterion }}</td>
                <td>{{ issue.wcag_level }}</td>
                <td>{{ issue.title }}</td>
                <td>{{ issue.description }}</td>
                <td class="page-url">{{ issue.page_url }}</td>
                <td>{{ issue.recommendation }}</td>
                <td>{% if issue.detected_by == 'vision_ai' %}视觉AI{% elif issue.detected_by == 'ai' %}AI{% else %}规则{% endif %}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>暂无检测问题</p>
    {% endif %}

    <div class="footer">
        <p>由 W4Agent 无障碍检测系统生成</p>
    </div>
</body>
</html>"""
