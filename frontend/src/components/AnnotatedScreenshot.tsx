import React, { useState } from 'react';
import { Image, Switch, Tooltip, Typography, Tag, Space } from 'antd';
import { getScreenshotUrl } from '../api/screenshots';
import type { Issue, PageInfo } from '../types/a11y';

const { Text } = Typography;

const severityColors: Record<string, string> = {
  critical: '#f5222d',
  major: '#fa8c16',
  minor: '#faad14',
  info: '#1677ff',
};

const severityLabels: Record<string, string> = {
  critical: '严重',
  major: '重要',
  minor: '一般',
  info: '提示',
};

interface AnnotatedScreenshotProps {
  page: PageInfo;
  issues: Issue[];
  onIssueClick?: (issue: Issue) => void;
}

const AnnotatedScreenshot: React.FC<AnnotatedScreenshotProps> = ({
  page,
  issues,
  onIssueClick,
}) => {
  const [showAnnotated, setShowAnnotated] = useState(true);

  const originalUrl = getScreenshotUrl(page.screenshot_path);
  const annotatedUrl = getScreenshotUrl(page.annotated_screenshot_path);
  const hasAnnotated = !!annotatedUrl;

  const currentUrl = showAnnotated && hasAnnotated ? annotatedUrl : originalUrl;

  if (!currentUrl) {
    return <Text type="secondary">暂无截图</Text>;
  }

  // Filter issues that belong to this page and have bounding boxes
  const pageIssues = issues.filter(
    (issue) => issue.page_id === page.id && issue.context?.bounding_box
  );

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <Space>
          <Text strong>{page.title || page.url}</Text>
          {hasAnnotated && (
            <Switch
              checkedChildren="标注"
              unCheckedChildren="原始"
              checked={showAnnotated}
              onChange={setShowAnnotated}
              size="small"
            />
          )}
        </Space>
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>{page.url}</Text>
        </div>
      </div>

      <div style={{ position: 'relative', display: 'inline-block' }}>
        <Image
          src={currentUrl}
          alt={`Screenshot of ${page.title || page.url}`}
          style={{ maxWidth: '100%', border: '1px solid #d9d9d9' }}
          preview={{ mask: '点击查看大图' }}
        />

        {/* Interactive overlay for non-annotated view */}
        {!showAnnotated && pageIssues.length > 0 && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
            }}
          >
            {pageIssues.map((issue) => {
              const bbox = issue.context!.bounding_box!;
              return (
                <Tooltip
                  key={issue.id}
                  title={
                    <div>
                      <div>
                        <Tag color={severityColors[issue.severity]} style={{ marginRight: 4 }}>
                          {severityLabels[issue.severity]}
                        </Tag>
                        <strong>{issue.title}</strong>
                      </div>
                      <div style={{ marginTop: 4, fontSize: 12 }}>{issue.description}</div>
                    </div>
                  }
                >
                  <div
                    style={{
                      position: 'absolute',
                      left: bbox.x,
                      top: bbox.y,
                      width: bbox.width,
                      height: bbox.height,
                      border: `2px solid ${severityColors[issue.severity] || '#1677ff'}`,
                      backgroundColor: `${severityColors[issue.severity] || '#1677ff'}15`,
                      cursor: onIssueClick ? 'pointer' : 'default',
                      pointerEvents: 'auto',
                    }}
                    onClick={() => onIssueClick?.(issue)}
                  />
                </Tooltip>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnnotatedScreenshot;
