export type IssueSeverity = 'critical' | 'major' | 'minor' | 'info';
export type IssueStatus = 'open' | 'confirmed' | 'false_positive' | 'fixed' | 'wont_fix';
export type WCAGLevel = 'A' | 'AA' | 'AAA';

export interface Issue {
  id: string;
  task_id: string;
  page_id: string;
  wcag_criterion: string;
  wcag_level: WCAGLevel;
  rule_id: string;
  severity: IssueSeverity;
  status: IssueStatus;
  title: string;
  description: string;
  recommendation: string | null;
  element_selector: string | null;
  element_html: string | null;
  screenshot_path: string | null;
  detected_by: string;
  confidence: number | null;
  jira_issue_key: string | null;
  created_at: string;
}

export interface PageInfo {
  id: string;
  task_id: string;
  url: string;
  title: string | null;
  status: string;
  depth: number;
  screenshot_path: string | null;
  created_at: string;
}
