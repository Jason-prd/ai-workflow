import { Card, Button, Tag } from 'antd';
import { PlayCircle, Edit, Clock, Zap } from 'lucide-react';
import type { Workflow } from '../types';

interface WorkflowCardProps {
  workflow: Workflow;
  onEdit: (id: string) => void;
  onRun: (id: string) => void;
}

const WorkflowCard = ({ workflow, onEdit, onRun }: WorkflowCardProps) => {
  const triggerTypeText = workflow.trigger.type === 'manual' ? '手动触发' : '定时触发';
  const statusColor = workflow.status === 'published' ? 'green' : 'orange';
  const statusText = workflow.status === 'published' ? '已发布' : '草稿';

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      hoverable
      onClick={() => onEdit(workflow.id)}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{workflow.name}</h3>
          <p className="text-gray-500 text-sm mt-1 line-clamp-2">{workflow.description}</p>
        </div>
        <Tag color={statusColor}>{statusText}</Tag>
      </div>
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <Zap size={14} />
          <span>{triggerTypeText}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock size={14} />
          <span>更新于 {formatDate(workflow.updatedAt)}</span>
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          type="primary"
          icon={<PlayCircle size={16} />}
          onClick={(e) => {
            e.stopPropagation();
            onRun(workflow.id);
          }}
        >
          运行
        </Button>
        <Button
          icon={<Edit size={16} />}
          onClick={(e) => {
            e.stopPropagation();
            onEdit(workflow.id);
          }}
        >
          编辑
        </Button>
      </div>
    </Card>
  );
};

export default WorkflowCard;