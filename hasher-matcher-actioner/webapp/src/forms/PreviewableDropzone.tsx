/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {SyntheticEvent, useCallback, useState} from 'react';
import {Container, Col, Row, Button, ResponsiveEmbed} from 'react-bootstrap';
import {useDropzone} from 'react-dropzone';

import '../styles/_dropzone.scss';
import {ContentType} from '../utils/constants';
import {BlurImage, BlurVideo} from '../utils/MediaUtils';

type FileType = 'video' | 'photo';

type PreviewPaneProps = {
  type: FileType;
  file: File;
  handleChange: () => void;
};

function PreviewPane({type, handleChange, file}: PreviewPaneProps) {
  const [revealed, setRevealed] = useState<boolean>(false);

  return (
    <Container>
      <Row>
        <Col className="text-right pb-2">
          <Button size="sm" variant="warning" onClick={handleChange}>
            Change
          </Button>{' '}
          <Button
            size="sm"
            variant="secondary"
            onClick={(e: SyntheticEvent) => {
              e.stopPropagation();
              setRevealed(!revealed);
            }}>
            {revealed ? 'Hide' : 'Reveal'}
          </Button>
        </Col>
      </Row>
      <Row>
        <Col>
          <ResponsiveEmbed aspectRatio="16by9">
            {type === 'video' ? (
              <BlurVideo src={URL.createObjectURL(file)} override={!revealed} />
            ) : (
              <BlurImage src={URL.createObjectURL(file)} override={!revealed} />
            )}
          </ResponsiveEmbed>
        </Col>
      </Row>
    </Container>
  );
}

type HelpTextProps = {
  isDragActive: boolean;
};

function HelpText({isDragActive}: HelpTextProps) {
  return isDragActive ? (
    <p>Drop the files here...</p>
  ) : (
    <p>Drag &apos;n&apos; drop some files here, or click to select file.</p>
  );
}

export type PreviewableDropzoneProps = {
  type: ContentType;
  file?: File;
  handleFileChange: (file: File) => void;
};

export default function PreviewableDropzone({
  type,
  file,
  handleFileChange,
}: PreviewableDropzoneProps) {
  // A dropzone for dnd and click-to-browse style file selection which can
  // preview select files. Previews are hidden by default.

  const onDrop = useCallback(acceptedFiles => {
    handleFileChange(acceptedFiles[0]);
  }, []);

  const {getRootProps, getInputProps, open, isDragActive} = useDropzone({
    onDrop,
    accept: type === ContentType.Video ? 'video/*' : 'image/*',
  });

  const fileType = type === ContentType.Video ? 'video' : 'photo';

  return (
    <div>
      {/* eslint-disable react/jsx-props-no-spreading */}
      <div {...getRootProps({className: 'dropzone', refKey: 'innerRef'})}>
        {/* eslint-disable react/jsx-props-no-spreading */}
        <input {...getInputProps()} />
        {file ? (
          <PreviewPane
            type={fileType}
            file={file}
            handleChange={() => open()}
          />
        ) : (
          <HelpText isDragActive={isDragActive} />
        )}
      </div>
    </div>
  );
}
