// WorkflowVisualizer.jsx
import React, { useMemo } from 'react';
import ReactFlow, {
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,      // ← Importato
  Position     // ← Importato
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction, ranksep: 120, nodesep: 60 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 60 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 90,
        y: nodeWithPosition.y - 30,
      },
      draggable: true,
    };
  });

  const layoutedEdges = edges.map((edge) => ({
    ...edge,
    type: 'default',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 12,
      height: 12,
    },
    animated: false,
    style: {
      stroke: '#555',
      strokeWidth: 2,
    },
  }));

  return { nodes: layoutedNodes, edges: layoutedEdges };
};

const ModuleNode = ({ data }) => {
  return (
    <div
      style={{
        background: '#4A90E2',
        borderRadius: '10px',
        padding: '14px 12px',
        color: 'white',
        boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
        minWidth: '180px',
        textAlign: 'center',
        fontSize: '14px',
        fontWeight: '600',
        border: '2px solid #2A5CAA',
        userSelect: 'none',
        position: 'relative',
      }}
    >
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#2A5CAA', width: 12, height: 12, borderRadius: '50%' }}
      />
      <div>🧩 {data.label}</div>
      <small
        style={{
          display: 'block',
          marginTop: '6px',
          fontSize: '11px',
          opacity: 0.9,
        }}
      >
        {data.ref?.split('/').pop() || 'module'}
      </small>
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#2A5CAA', width: 12, height: 12, borderRadius: '50%' }}
      />
    </div>
  );
};

const nodeTypes = { moduleNode: ModuleNode };

export default function WorkflowVisualizer({ workflow }) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!workflow) return { nodes: [], edges: [] };

    const nodes = workflow.elements.nodes.map((n) => ({
      id: n.data.id,
      type: 'moduleNode',
      data: { label: n.data.label, ref: n.data.ref },
      position: { x: 0, y: 0 },
      draggable: true,
    }));

    const edges = workflow.elements.edges.map((e) => ({
      id: e.data.id,
      source: e.data.source,
      target: e.data.target,
      label: `${e.data.source_port} → ${e.data.target_port}`,
      labelStyle: {
        fill: '#333',
        fontWeight: '500',
        fontSize: '12px',
        background: '#fff',
        padding: '2px 6px',
        borderRadius: '4px',
      },
      animated: false,
    }));

    return getLayoutedElements(nodes, edges);
  }, [workflow]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable={true}
      nodesConnectable={false}
      elementsSelectable={true}
      panOnScroll={true}
      minZoom={0.2}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
    >
      <Controls />
      <MiniMap position="bottom-right" />
      <Background color="#f0f0f0" gap={16} />
    </ReactFlow>
  );
}
