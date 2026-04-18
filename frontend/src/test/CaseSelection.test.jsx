import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import CaseSelection from '../components/CaseSelection';

describe('CaseSelection', () => {
  const mockCases = [
    { 
      id: 1, 
      number: '123', 
      plaintiff: 'Maria', 
      risk: 'Baixo', 
      type: 'Consignado', 
      value: 'R$ 10', 
      recommendation: 'DEFESA' 
    }
  ];

  it('deve renderizar a lista de casos', () => {
    render(<CaseSelection cases={mockCases} onSelectCase={() => {}} />);
    expect(screen.getByText('Maria')).toBeInTheDocument();
    expect(screen.getByText('123')).toBeInTheDocument();
  });

  it('deve chamar onSelectCase ao clicar em um card', () => {
    const onSelectCase = vi.fn();
    render(<CaseSelection cases={mockCases} onSelectCase={onSelectCase} />);
    
    const card = screen.getByText('Maria').closest('.case-row');
    fireEvent.click(card);
    
    expect(onSelectCase).toHaveBeenCalledWith(mockCases[0]);
  });

  it('deve exibir mensagem de erro se não houver casos', () => {
    render(<CaseSelection cases={[]} onSelectCase={() => {}} />);
    expect(screen.getByText('Nenhum processo encontrado')).toBeInTheDocument();
  });
});
