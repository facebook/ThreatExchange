/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import {findAllByTestId} from '@testing-library/react';
import classNames from 'classnames';
import React, {useState} from 'react';
import {Image} from 'react-bootstrap';

import '../styles/_image_blur.scss';

type BlurUntilHoverImageProps = {
  src: string;
  override?: boolean;
};

/**
 * Show a blurred version of an image at {src}. If override is given value of
 * true or false, it will blur or not blur respectively. If not provided at all,
 * it will unblur on hover.
 */
export function BlurImage({src, override}: BlurUntilHoverImageProps) {
  const [blurred, setBlurred] = useState(false);

  function handleMouseLeave() {
    if (override === undefined) {
      setBlurred(true);
    }
  }

  function handleMouseEnter() {
    if (override === undefined) {
      setBlurred(false);
    }
  }

  const actualBlurred = override === undefined ? blurred : override;

  return src ? (
    <Image
      onMouseLeave={handleMouseLeave}
      onMouseEnter={handleMouseEnter}
      className={classNames({'image-preview': true, blur: actualBlurred})}
      src={src}
      fluid
      rounded
    />
  ) : (
    <span className="sr-only">Loading...</span>
  );
}

BlurImage.defaultProps = {
  override: undefined,
};

export default BlurImage;
