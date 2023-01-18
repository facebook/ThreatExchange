/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Container, Row, Col} from 'react-bootstrap';

type FixedWidthCenterAlignedLayoutProps = {
  title?: string;
  children: JSX.Element | JSX.Element[];
};

/**
 * Uses a bootstrap container to put all content in the center of the main area.
 * Supports a title and any children.
 *
 * If title is not provided, does not provide the top row. You should provide
 * your own.
 *
 * Does not provide rows and cols. That is for pages to provide.
 *
 * A page impl using this class would look like.
 *
 * ```
 * return (
 *   <FixedWidthCenterAlignedLayout title="Recipe Details">
 *     <Row>
 *       <Col>
 *         ... your content here.
 *       </Col>
 *     </Row>
 *   </FixedWidthCenterAlignedLayout>
 * )
 * ```
 *
 * Centralizing the layouts like this allows page authors to focus on the page.
 */
export default function FixedWidthCenterAlignedLayout({
  title,
  children = [],
}: FixedWidthCenterAlignedLayoutProps): JSX.Element {
  return (
    <Container>
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

FixedWidthCenterAlignedLayout.defaultProps = {
  title: undefined,
};
