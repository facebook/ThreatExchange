/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {Button, Col, Container, Row} from 'react-bootstrap';

import {BlurImage} from '../utils/ImageUtils';
import {ContentType} from '../utils/constants';
import {CopyableTextField} from '../utils/TextFieldsUtils';

function renderImage(url: string, revealed: boolean): JSX.Element {
  return <BlurImage src={url} override={!revealed} />;
}

function swtchContentTypeRenderers(
  revealed: boolean,
  contentType: ContentType,
  url?: string,
  raw?: string,
) {
  switch (contentType) {
    case ContentType.Photo:
      return renderImage(url!, revealed);
    default:
      return <div>`No renderer found for type ${contentType}`</div>;
  }
}

type ContentPreviewProps = {
  contentType: ContentType;
  contentId: string;
  url?: string;
  raw?: string;
};

/**
 * Shows preview for images, videos, text.
 *
 * For all cases, shows the content_id in a copyable format, and then a button
 * to unobfuscate the content and then the obfuscated content.
 */
export default function ContentPreview({
  contentType,
  contentId,
  url,
  raw,
}: ContentPreviewProps) {
  const [revealed, setRevealed] = useState(false);

  return (
    <Container>
      <Row className="my-2">
        <Col>
          <span>
            <strong>ContentId:&nbsp;</strong>
          </span>
          <CopyableTextField
            color="black"
            tooltip="Copy content_id."
            text={contentId}
          />
        </Col>
      </Row>
      <Row className="my-2">
        <Col>
          <Button onClick={() => setRevealed(!revealed)}>
            {revealed ? 'Hide!' : 'Reveal!'}
          </Button>
        </Col>
      </Row>
      <Row className="my-2">
        <Col>{swtchContentTypeRenderers(revealed, contentType, url, raw)}</Col>
      </Row>
    </Container>
  );
}

ContentPreview.defaultProps = {
  url: undefined,
  raw: undefined,
};
