// app.jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import WorkflowVisualizer from './WorkflowVisualizer.jsx';

// Carica i dati generati da Python
import { graphData } from './graphData.js';

const root = createRoot(document.getElementById('root'));
root.render(<WorkflowVisualizer workflow={graphData} />);
