/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Col, Button} from 'react-bootstrap';

type HasChildrenOnlyProps = {
  children: string | JSX.Element | JSX.Element[];
};

/**
 * Use within a bootstrap row to create a thematically consistent empty state
 * across pages.
 *
 * Usage:
 * <EmptyState>
 *   <EmptyState.Lead>What you want the empty state to say</EmptyState.Lead>
 *   <EmptyState.CTA onClick={}>Do the thing!</EmptyState.CTA>
 * </EmptyState>
 */
export default function EmptyState({
  children,
}: HasChildrenOnlyProps): JSX.Element {
  return (
    <Col xs={{offset: 2, span: 8}} className="py-4">
      <div className="h-100" style={{textAlign: 'center', paddingTop: '40%)'}}>
        {children}
      </div>
    </Col>
  );
}

EmptyState.Lead = function ({children}: HasChildrenOnlyProps): JSX.Element {
  return <p className="lead">{children}</p>;
};

type CTAProps = HasChildrenOnlyProps & {
  onClick: () => void;
};

EmptyState.CTA = function ({children, onClick}: CTAProps): JSX.Element {
  return (
    <p className="text-center">
      <Button variant="success" size="lg" onClick={onClick}>
        {children}
      </Button>
    </p>
  );
};
