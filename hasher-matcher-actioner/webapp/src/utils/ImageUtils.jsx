/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {Image} from 'react-bootstrap';

export const BlurUntilHoverImage =
  // eslint-disable-next-line react/prop-types
  ({src}) => {
    const imgStyleBlur = {
      border: 'none',
      filter: 'blur(10px) grayscale(100%)',
      margin: '4px 4px 4px 4px',
      maxHeight: '450px',
      maxWidth: '450px',
    };

    const imgStyleNoBlur = {...imgStyleBlur, filter: 'none'};
    const [style, setStyle] = useState(imgStyleBlur);

    return src ? (
      <Image
        onMouseLeave={() => setStyle(imgStyleBlur)}
        onMouseEnter={() => {
          setStyle(imgStyleNoBlur);
        }}
        style={style}
        src={src}
        fluid
        rounded
      />
    ) : (
      <span className="sr-only">Loading...</span>
    );
  };

export default BlurUntilHoverImage;
