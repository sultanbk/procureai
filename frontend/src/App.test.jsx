import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';
import { ToastProvider } from './components/ui/ToastProvider.jsx';

describe('App Component', () => {
  it('renders the application correctly', () => {
    render(
      <ToastProvider>
        <App />
      </ToastProvider>
    );
    const elements = screen.getAllByText(/ProcureAI/i);
    expect(elements.length).toBeGreaterThan(0);
  });
});
