/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import classNames from 'classnames';
import React, {useState} from 'react';
import {Image} from 'react-bootstrap';

import '../styles/_media_blur.scss';

type BlurUntilHoverImageProps = {
  src: string;
  override?: boolean;
};

function BlurMedia(
  renderFn: (
    handleMouseLeave: () => void,
    handleMouseEnter: () => void,
    blur: boolean,
    src: string,
  ) => JSX.Element,
): ({src, override}: BlurUntilHoverImageProps) => JSX.Element {
  function BlurMediaInner({src, override}: BlurUntilHoverImageProps) {
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
      renderFn(handleMouseLeave, handleMouseEnter, actualBlurred, src)
    ) : (
      <span className="sr-only">Loading...</span>
    );
  }

  BlurMediaInner.defaultProps = {
    override: undefined,
  };

  return BlurMediaInner;
}

/**
 * Show a blurred version of an image at {src}. If override is given value of
 * true or false, it will blur or not blur respectively. If not provided at all,
 * it will unblur on hover.
 */
export const BlurImage = BlurMedia(
  (handleMouseLeave, handleMouseEnter, blur, src): JSX.Element => (
    <Image
      onMouseLeave={handleMouseLeave}
      onMouseEnter={handleMouseEnter}
      className={classNames({'image-preview': true, blur})}
      src={src}
      fluid
      rounded
    />
  ),
);

/**
 * Show a blurred preview of a video at {src}.
 */
export const BlurVideo = BlurMedia(
  (handleMouseLeave, handleMouseEnter, blur, src): JSX.Element => (
    <div className="video-preview-container">
      {/* eslint-disable jsx-a11y/media-has-caption */}
      <video
        onMouseLeave={handleMouseLeave}
        onMouseEnter={handleMouseEnter}
        className={classNames({'video-preview': true, blur})}
        src={src}
        controls
      />
    </div>
  ),
);
