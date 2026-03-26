import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import GlobalGraph from './components/GlobalGraph';
import KnowledgeGraph from './components/KnowledgeGraph';
import FileDetailView from './components/FileDetailView';
import QAView from './components/QAView';
import { Network, Database, MessageSquare, BookOpen } from 'lucide-react';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <nav className="side-nav">
          <div className="logo">IND 智慧图谱系统</div>
          
          <div className="nav-group">核心视图</div>
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Network size={18} /> 文档语义关联
          </NavLink>
          <NavLink to="/knowledge-graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Database size={18} /> 本体知识图谱
          </NavLink>
          
          <div className="nav-group">辅助功能</div>
          <NavLink to="/qa" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <MessageSquare size={18} /> RAG 智能问答
          </NavLink>
          
          <div className="mt-auto pt-6 border-t border-white/5">
            <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10">
              <div className="flex items-center gap-2 text-indigo-400 mb-2">
                <BookOpen size={16} />
                <span className="text-xs font-bold uppercase tracking-wider">系统状态</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-relaxed">
                当前加载: 正大天晴注册案例<br/>
                解析引擎: MinerU v0.6<br/>
                图谱节点: 实时计算
              </p>
            </div>
          </div>
        </nav>

        <main className="view-pane">
          <Routes>
            <Route path="/" element={<GlobalGraph />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
            <Route path="/file/:filename" element={<FileDetailView />} />
            <Route path="/qa" element={<QAView />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
