/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Button, Col, Container, ResponsiveEmbed, Row} from 'react-bootstrap';

import {BlurImage, BlurVideo} from '../utils/MediaUtils';
import {ContentType} from '../utils/constants';
import {CopyableTextField} from '../utils/TextFieldsUtils';

function renderImage(url: string, revealed: boolean): JSX.Element {
  return <BlurImage src={url} override={!revealed} />;
}

function renderVideo(url: string, revealed: boolean): JSX.Element {
  /* eslint-disable jsx-a11y/media-has-caption */
  return <BlurVideo src={url} override={!revealed} />;
}

function swtchContentTypeRenderers(
  revealed: boolean,
  contentType: ContentType,
  url = '',
) {
  switch (contentType) {
    case ContentType.Photo:
      return renderImage(url, revealed);
    case ContentType.Video:
      return renderVideo(url, revealed);
    default:
      return <div>{`No renderer found for type ${contentType}`}</div>;
  }
}

type ContentPreviewProps = {
  contentType: ContentType;
  contentId: string;
  url?: string;
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
}: ContentPreviewProps): JSX.Element {
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
            {revealed ? 'Hide' : 'Reveal'}
          </Button>
        </Col>
      </Row>
      <Row className="my-2">
        <Col>
          <ResponsiveEmbed aspectRatio="16by9">
            {swtchContentTypeRenderers(revealed, contentType, url)}
          </ResponsiveEmbed>
        </Col>
      </Row>
    </Container>
  );
}

ContentPreview.defaultProps = {
  url: undefined,
};
