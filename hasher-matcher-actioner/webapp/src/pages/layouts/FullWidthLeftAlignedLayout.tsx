/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Container, Row, Col} from 'react-bootstrap';

type FullWidthLeftAlignedLayoutProps = {
  title?: string;
  children: JSX.Element | JSX.Element[];
};

/**
 * Uses a bootstrap container to put content in the center left aligned of the main area.
 * Supports a title and any children.
 *
 * fluid version of FixedWidthCenterAlignedLayout (see that file for more details on usage)
 */
export default function FullWidthLeftAlignedLayout({
  title,
  children = [],
}: FullWidthLeftAlignedLayoutProps): JSX.Element {
  return (
    <Container fluid>
      {title !== undefined ? (
        <Row>
          <Col className="mt-4">
            <h1>{title}</h1>
          </Col>
        </Row>
      ) : null}
      {children}
    </Container>
  );
}

FullWidthLeftAlignedLayout.defaultProps = {
  title: undefined,
};
