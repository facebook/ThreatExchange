/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Container} from 'react-bootstrap';

type SettingsTabPaneProps = {
  children: JSX.Element | JSX.Element[];
};

/**
 * Wrap settings pages in this class. Allows you to change their properties
 * together. And allows you to left align the page while retaining fixed-width
 * properties.
 *
 * @returns
 */
export default function SettingsTabPane({
  children = [],
}: SettingsTabPaneProps): JSX.Element {
  return (
    <Container
      className="mt-4"
      style={{marginLeft: 'unset', marginRight: 'unset'}}>
      {children}
    </Container>
  );
}

type SettingsTabPaneTitleProps = {
  children: string;
};

SettingsTabPane.Title = function Title({
  children,
}: SettingsTabPaneTitleProps): JSX.Element {
  return <h2>{children}</h2>;
};
