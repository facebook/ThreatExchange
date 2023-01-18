/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import axios from 'axios';
import {Modal, Container, Row, Col} from 'react-bootstrap';
import {ContentType} from '../../utils/constants';
import BankMemberForm from '../../forms/BankMemberForm';
import {addBankMember, fetchMediaUploadURL} from '../../Api';

type AddBankMemberModalProps = {
  bankId: string;
  bankName: string;
  show: boolean;
  contentType: ContentType;
  onCloseClick: (didAdd: boolean) => void;
};

function putFileWithProgress(
  url: string,
  file: File,
  progressCallback: (progress: number) => void,
): Promise<void> {
  const config = {
    // Can't type the following line any better. Even axios types leave it as any!
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onUploadProgress(progressEvent: any) {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total,
      );
      progressCallback(percentCompleted);
    },
    headers: {
      'Content-Type': file.type,
    },
  };

  return axios.put(url, file, config).then(() => {
    progressCallback(100);
  });
}

export default function AddBankMemberModal({
  show,
  bankId,
  bankName,
  contentType,
  onCloseClick,
}: AddBankMemberModalProps): JSX.Element {
  let title;
  switch (contentType) {
    case ContentType.Photo:
      title = `Add a Photo to ${bankName}`;
      break;
    case ContentType.Video:
      title = `Add a Video to ${bankName}`;
      break;
    default:
      title = 'Unsupported content type';
  }

  const [fileUploadProgress, setFileUploadProgress] = useState<number>(0);

  const closeWrapper = (didAdd = false) => {
    setFileUploadProgress(0);
    onCloseClick(didAdd);
  };

  const handleSubmit = (file: File, notes: string, tags: string[]) => {
    // Mark upload in progress:
    setFileUploadProgress(1);

    const fileNameParts = file.name.split('.');
    const extension = `.${fileNameParts[fileNameParts.length - 1]}`;

    // Obtain a media URL
    fetchMediaUploadURL(file.type, extension).then(response => {
      // Put file on media URL
      putFileWithProgress(response.upload_url, file, setFileUploadProgress)
        .then(() =>
          // Add bank member to media URL
          addBankMember(
            bankId,
            contentType,
            response.storage_bucket,
            response.storage_key,
            notes,
            tags,
          ),
        )
        .then(() => closeWrapper(true));
    });
  };

  return (
    <Modal show={show} onHide={closeWrapper} size="lg" centered>
      <Modal.Header closeButton onHide={() => closeWrapper()}>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Container>
          <Row>
            <Col>
              <BankMemberForm
                type={contentType}
                uploadProgress={fileUploadProgress}
                handleSubmit={handleSubmit}
              />
            </Col>
          </Row>
        </Container>
      </Modal.Body>
    </Modal>
  );
}
