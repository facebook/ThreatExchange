/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {Container, Row, Col} from 'react-bootstrap';

type FixedWidthCenterAlignedLayoutProps = {
  title: string;
  children: JSX.Element | JSX.Element[];
};

/**
 * Uses a bootstrap container to put all content in the center of the main area.
 * Supports a title and any children.
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
 * Centralizing the layouts like this allows page authors to focus on the
 * page.
 */
export default function FixedWidthCenterAlignedLayout({
  title,
  children = [],
}: FixedWidthCenterAlignedLayoutProps): JSX.Element {
  return (
    <Container>
      <Row>
        <Col className="mt-4">
          <h1>{title}</h1>
        </Col>
      </Row>
      {children}
    </Container>
  );
}
