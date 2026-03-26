import { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import axios from 'axios';
import { Loader2, Info, Link as LinkIcon, ExternalLink } from 'lucide-react';

interface KGNode {
  id: string;
  label: string;
  type: 'Class' | 'Instance';
  group: number;
  description?: string;
}

interface KGLink {
  source: string;
  target: string;
  label: string;
  value: number;
  source_context?: string;
  source_location?: string;
  source_md?: string;
}

interface KGData {
  nodes: KGNode[];
  links: KGLink[];
}

const KnowledgeGraph = () => {
  const [data, setData] = useState<KGData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const [selectedLink, setSelectedLink] = useState<KGLink | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchKG = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/graph/knowledge');
        setData(response.data);
      } catch (error) {
        console.error('Failed to fetch knowledge graph:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchKG();
  }, []);

  const getNodeColor = (node: KGNode) => {
    if (node.type === 'Class') return '#f59e0b'; // Amber for Classes
    return '#6366f1'; // Indigo for Instances
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-[#0a0a0c]">
        <Loader2 className="animate-spin text-indigo-500 w-10 h-10" />
      </div>
    );
  }

  return (
    <div className="w-full h-full relative flex overflow-hidden bg-[#0a0a0c]" ref={containerRef}>
      {/* 图谱主区域 */}
      <div className="flex-1 relative">
        <div className="absolute top-6 left-6 z-10 glass p-5 rounded-2xl max-w-sm pointer-events-none">
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
             本体驱动知识图谱
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            基于 IND 本体模型自动抽取的结构化事实。
            <br/><span className="text-amber-500 font-bold">●</span> 本体类 (TBox) 
            <span className="text-indigo-500 font-bold ml-2">●</span> 实例事实 (ABox)
          </p>
        </div>

        <ForceGraph2D
          graphData={data}
          nodeLabel="id"
          nodeColor={getNodeColor}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.1}
          linkLabel={(d: any) => d.label}
          linkWidth={1.5}
          linkColor={() => 'rgba(255, 255, 255, 0.15)'}
          onNodeClick={(node: any) => {
            setSelectedNode(node);
            setSelectedLink(null);
          }}
          onLinkClick={(link: any) => {
            setSelectedLink(link);
            setSelectedNode(null);
          }}
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.id;
            const fontSize = node.type === 'Class' ? 14 / globalScale : 11 / globalScale;
            ctx.font = `${node.type === 'Class' ? 'bold' : 'normal'} ${fontSize}px Inter`;
            
            // Draw circle
            const r = node.type === 'Class' ? 6 : 4;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
            ctx.fillStyle = getNodeColor(node);
            ctx.fill();
            
            // Add glow for classes
            if (node.type === 'Class') {
                ctx.shadowBlur = 15;
                ctx.shadowColor = '#f59e0b';
            } else {
                ctx.shadowBlur = 0;
            }

            // Draw label
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = node.type === 'Class' ? '#f59e0b' : '#e2e8f0';
            ctx.fillText(label, node.x, node.y + r + fontSize + 2);
          }}
        />
      </div>

      {/* 侧边详情面板 */}
      <aside className={`w-96 bg-[#111114] border-l border-white/5 p-6 overflow-y-auto transition-transform duration-300 ${selectedNode || selectedLink ? 'translate-x-0' : 'translate-x-full absolute right-0'}`}>
        {(selectedNode || selectedLink) && (
          <div className="space-y-6 slide-in">
            <div className="flex justify-between items-start">
              <h3 className="text-xl font-bold text-white">详情信息</h3>
              <button 
                onClick={() => { setSelectedNode(null); setSelectedLink(null); }}
                className="text-slate-500 hover:text-white transition-colors"
              >
                关闭
              </button>
            </div>

            {selectedNode && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-xs uppercase tracking-widest text-indigo-400 font-bold mb-1">
                    {selectedNode.type === 'Class' ? '本体类 (TBox)' : '实例节点 (ABox)'}
                  </div>
                  <div className="text-2xl font-bold text-white">{selectedNode.label}</div>
                </div>
                
                {selectedNode.description && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                      <Info size={14} /> 描述定义
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed bg-white/5 p-4 rounded-xl border border-white/5">
                      {selectedNode.description}
                    </p>
                  </div>
                )}
              </div>
            )}

            {selectedLink && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-xs uppercase tracking-widest text-emerald-400 font-bold mb-1">关系路径 (Predicate)</div>
                  <div className="flex items-center gap-3 text-white font-medium">
                    <span>{typeof selectedLink.source === 'object' ? (selectedLink.source as any).id : selectedLink.source}</span>
                    <LinkIcon size={14} className="text-emerald-500" />
                    <span className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-xs">{selectedLink.label}</span>
                    <LinkIcon size={14} className="text-emerald-500" />
                    <span>{typeof selectedLink.target === 'object' ? (selectedLink.target as any).id : selectedLink.target}</span>
                  </div>
                </div>

                {selectedLink.source_context && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                       事实来源 (ABox Traceability)
                    </div>
                    <div className="bg-white/5 p-4 rounded-xl border border-white/5 space-y-3">
                      <p className="text-sm text-slate-200 italic leading-relaxed">
                        "{selectedLink.source_context}"
                      </p>
                      <div className="pt-3 border-t border-white/5 flex flex-col gap-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-500">来源文档:</span>
                          <span className="text-indigo-300 font-medium">{selectedLink.source_md || '未知文档'}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-500 flex items-center gap-1">
                             溯源位置: {selectedLink.source_location}
                          </span>
                          <button className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                            查看原文 <ExternalLink size={10} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
};

export default KnowledgeGraph;
