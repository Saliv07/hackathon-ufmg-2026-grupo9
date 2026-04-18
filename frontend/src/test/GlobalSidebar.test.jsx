import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import GlobalSidebar from '../components/GlobalSidebar';

describe('GlobalSidebar', () => {
  const mockCases = [
    { id: 1, plaintiff: 'Maria das Graças' },
    { id: 2, plaintiff: 'José Raimundo' }
  ];



  it('deve listar os casos recentes', () => {
    render(<GlobalSidebar cases={mockCases} currentView="dashboard" onNavigate={() => {}} onSelectCase={() => {}} />);
    expect(screen.getByText('Maria das Graças')).toBeInTheDocument();
    expect(screen.getByText('José Raimundo')).toBeInTheDocument();
  });


});
