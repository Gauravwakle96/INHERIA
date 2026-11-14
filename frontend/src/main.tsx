import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import '@fontsource/inter/latin-700.css';
import '@xyflow/react/dist/style.css';
import './styles.css';
import { App } from './App';
import { ThemeProvider } from './ThemeProvider';
import { ApiError } from './api';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: (count, error) => count < 1 && !(error instanceof ApiError && [401, 403, 404, 409, 422, 429].includes(error.status)), staleTime: 30_000, refetchOnWindowFocus: true } } });
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><ThemeProvider><QueryClientProvider client={queryClient}><BrowserRouter><App /></BrowserRouter></QueryClientProvider></ThemeProvider></React.StrictMode>);
