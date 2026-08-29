import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ReportPage from '../ReportPage';

describe('ReportPage', () => {
  it('renders Report Page heading and parameter runId', () => {
    render(
      <MemoryRouter initialEntries={['/report/test-run-123']}>
        <Routes>
          <Route path="/report/:runId" element={<ReportPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByRole('heading', { name: /report page/i })).toBeInTheDocument();
    expect(screen.getByText(/run id: test-run-123/i)).toBeInTheDocument();
  });
});
