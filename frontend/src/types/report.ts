export interface Report {
  id: string;
  task_id: string;
  overall_score: number;
  level_a_score: number;
  level_aa_score: number;
  level_aaa_score: number;
  total_pages: number;
  total_issues: number;
  critical_issues: number;
  major_issues: number;
  minor_issues: number;
  summary: string | null;
  recommendations: string | null;
  issue_breakdown: Record<string, unknown> | null;
  page_results: Record<string, unknown> | null;
  html_path: string | null;
  pdf_path: string | null;
  json_path: string | null;
  created_at: string;
}
