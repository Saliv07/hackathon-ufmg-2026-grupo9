import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import GlobalSidebar from '../components/GlobalSidebar';

describe('GlobalSidebar', () => {
  const mockCases = [
    { id: 1, plaintiff: 'Maria das Graças' },
    { id: 2, plaintiff: 'José Raimundo' }
  ];

  it('deve renderizar o logo da Enter.ai', () => {
    render(<GlobalSidebar cases={mockCases} currentView="dashboard" onNavigate={() => {}} onSelectCase={() => {}} />);
    const logo = screen.getByAltText(/Enter.ai Logo/i);
    expect(logo).toBeInTheDocument();
  });

  it('deve listar os casos recentes', () => {
    render(<GlobalSidebar cases={mockCases} currentView="dashboard" onNavigate={() => {}} onSelectCase={() => {}} />);
    expect(screen.getByText('Maria das Graças')).toBeInTheDocument();
    expect(screen.getByText('José Raimundo')).toBeInTheDocument();
  });

  it('deve exibir o botão de Novo Processo', () => {
    render(<GlobalSidebar cases={mockCases} currentView="dashboard" onNavigate={() => {}} onSelectCase={() => {}} />);
    expect(screen.getByText('Novo Processo')).toBeInTheDocument();
  });
});
