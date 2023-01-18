/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import {IonIcon} from '@ionic/react';
import classNames from 'classnames';
import {eye, eyeOff} from 'ionicons/icons';
import React, {useState} from 'react';
import {Button, Image} from 'react-bootstrap';

import '../styles/_media_blur.scss';

type BlurUntilHoverImageProps = {
  src: string;
  override?: boolean;
};

function BlurMedia(
  renderFn: (blur: boolean, src: string) => JSX.Element,
): ({src, override}: BlurUntilHoverImageProps) => JSX.Element {
  function BlurMediaInner({src, override}: BlurUntilHoverImageProps) {
    const [blurred, setBlurred] = useState(true);

    const toggle = () => {
      if (override === undefined) {
        setBlurred(!blurred);
      }
    };

    const actualBlurred = override === undefined ? blurred : override;

    return src ? (
      <div className="blur-friendly-preview-container">
        {override === undefined ? (
          <Button className="eye" size="sm" variant="warning" onClick={toggle}>
            <IonIcon size="large" icon={actualBlurred ? eye : eyeOff} />
          </Button>
        ) : null}
        {renderFn(actualBlurred, src)}
      </div>
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
  (blur, src): JSX.Element => (
    <Image
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
  (blur, src): JSX.Element => (
    /* eslint-disable jsx-a11y/media-has-caption */
    <video
      className={classNames({'video-preview': true, blur})}
      src={src}
      controls
    />
  ),
);
