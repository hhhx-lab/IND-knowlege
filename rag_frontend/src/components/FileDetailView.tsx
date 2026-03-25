import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactFlow, { 
  type Node, 
  type Edge, 
  Background, 
  Controls, 
  Handle,
  Position,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ArrowLeft, BookOpen, Hash, BarChart3, Loader2 } from 'lucide-react';

// Custom Node Component for Mind Map
const MindMapNode = ({ data }: any) => {
  return (
    <div className={`mind-node ${data.active ? 'active' : ''}`} style={{
      padding: '8px 16px',
      borderRadius: '8px',
      border: '2px solid',
      borderColor: data.active ? '#6366f1' : '#334155',
      backgroundColor: data.active ? '#4338ca' : '#1e293b',
      color: data.active ? '#ffffff' : '#e2e8f0',
      fontSize: '13px',
      fontWeight: '500',
      transition: 'all 0.2s',
      boxShadow: data.active ? '0 0 15px rgba(99, 102, 241, 0.4)' : 'none'
    }}>
      <Handle type="target" position={Position.Left} style={{ visibility: 'hidden' }} />
      {data.label}
      <Handle type="source" position={Position.Right} style={{ visibility: 'hidden' }} />
    </div>
  );
};

const nodeTypes = {
  mindMap: MindMapNode,
};

const FileDetailView = () => {
  const { filename } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [fileData, setFileData] = useState<any>(null);
  const [selectedSection, setSelectedSection] = useState<any>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const transformToFlow = (structure: any[]) => {
    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];
    let idCounter = 0;

    const traverse = (children: any[], parentId: string | null, x: number, y: number) => {
      const verticalGap = 70;
      const horizontalGap = 240;
      
      children.forEach((item, index) => {
        const id = `node-${idCounter++}`;
        const currentY = y + index * verticalGap;
        const currentX = x + horizontalGap;

        flowNodes.push({
          id,
          type: 'mindMap',
          data: { label: item.title, content: item.content, active: false },
          position: { x: currentX, y: currentY },
        });

        if (parentId) {
          flowEdges.push({
            id: `edge-${parentId}-${id}`,
            source: parentId,
            target: id,
            animated: true,
            style: { stroke: '#6366f1', strokeWidth: 2 }
          });
        }

        if (item.children && item.children.length > 0) {
          traverse(item.children, id, currentX, currentY);
        }
      });
    };

    const rootId = 'root-file';
    flowNodes.push({
      id: rootId,
      type: 'mindMap',
      data: { label: filename, content: '请从思维导图中选择章节查看内容。', active: true },
      position: { x: 0, y: 150 },
    });

    traverse(structure, rootId, 0, 100);
    return { nodes: flowNodes, edges: flowEdges };
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/file/details?filename=${encodeURIComponent(filename || '')}`);
        setFileData(response.data);
        const { nodes: flowNodes, edges: flowEdges } = transformToFlow(response.data.structure);
        setNodes(flowNodes);
        setEdges(flowEdges);
        setSelectedSection({ title: filename, content: '请点击左侧思维导图中的节点以查看详细文本内容。' });
      } catch (error) {
        console.error('Failed to fetch file details:', error);
      } finally {
        setLoading(false);
      }
    };

    if (filename) fetchData();
  }, [filename]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedSection({ title: node.data.label, content: node.data.content });
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, active: n.id === node.id },
      }))
    );
  }, [setNodes]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%', backgroundColor: '#0a0a0c' }}>
        <Loader2 className="animate-spin" style={{ color: '#6366f1', width: '40px', height: '40px' }} />
      </div>
    );
  }

  return (
    <div className="detail-view-container fade-in">
      <header className="detail-header">
        <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: '600', margin: 0 }}>{filename}</h1>
          <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>文档结构扫描与关键要素抽取</p>
        </div>
      </header>

      <div className="main-layout">
        <section className="mind-map-section">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1e293b" gap={20} />
            <Controls />
          </ReactFlow>
        </section>

        <section className="content-section">
          <div className="content-header">
            <h3 style={{ fontSize: '14px', fontWeight: '700', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase' }}>
              <BookOpen size={16} /> 当前章节：{selectedSection?.title}
            </h3>
          </div>
          <div className="content-body">
            {selectedSection?.content ? (
              <div>
                {selectedSection.content.split('\n').map((line: string, i: number) => (
                  <p key={i} style={{ marginBottom: '16px' }}>{line}</p>
                ))}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569', gap: '16px' }}>
                <BookOpen size={48} style={{ opacity: 0.2 }} />
                <p>本章节暂无文本内容</p>
              </div>
            )}
          </div>
        </section>

        <aside className="analytics-aside">
          <div style={{ marginBottom: '32px' }}>
            <h4 style={{ fontSize: '12px', fontWeight: '700', color: '#e2e8f0', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase' }}>
              <Hash size={16} style={{ color: '#6366f1' }} /> 核心关键词
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {fileData?.keywords?.map((kw: string, i: number) => (
                <span key={i} className="badge">{kw}</span>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '32px' }}>
            <h4 style={{ fontSize: '12px', fontWeight: '700', color: '#e2e8f0', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase' }}>
              <BarChart3 size={16} style={{ color: '#c084fc' }} /> 高频检索词
            </h4>
            <div>
              {fileData?.hf_words?.map((hw: string, i: number) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <span style={{ color: '#94a3b8' }}>{hw}</span>
                  <span style={{ color: '#6366f1', opacity: 0.8 }}>{(0.9 - i * 0.05).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 style={{ fontSize: '12px', fontWeight: '700', color: '#e2e8f0', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase' }}>
              <BookOpen size={16} style={{ color: '#10b981' }} /> 文档摘要
            </h4>
            <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: '1.6', background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
              {fileData?.summary || "正在提取文档摘要..."}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default FileDetailView;
