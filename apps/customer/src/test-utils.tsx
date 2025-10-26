// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// Testing utilities to render components with routing and auth context.
/* eslint-disable react-refresh/only-export-components */

import { render } from '@testing-library/react';
import { createMemoryHistory } from 'history';
import {
  type RouteObject,
  unstable_HistoryRouter as HistoryRouter,
  useRoutes,
} from 'react-router-dom';
import { AuthProvider } from './lib/authContext';

export interface RenderWithRouterOptions {
  initialEntries?: string[];
}

export function renderWithRouter(
  routes: RouteObject[],
  options: RenderWithRouterOptions = {},
) {
  const history = createMemoryHistory({
    initialEntries: options.initialEntries ?? ['/'],
  });

  function RoutesContainer() {
    const element = useRoutes(routes);
    return <AuthProvider>{element}</AuthProvider>;
  }

  const rendered = render(
    <HistoryRouter history={history}>
      <RoutesContainer />
    </HistoryRouter>,
  );

  return {
    history,
    ...rendered,
  };
}

export * from '@testing-library/react';
export { render } from '@testing-library/react';
