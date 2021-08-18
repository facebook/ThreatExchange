/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Col, Row, Spinner} from 'react-bootstrap';
import {useParams} from 'react-router-dom';
import {fetchContentPipelineProgress} from '../Api';
import ContentPreview from '../components/ContentPreview';
import ContentProgressStepper from '../components/ContentProgressStepper';
import {ContentType} from '../utils/constants';
import {toDate} from '../utils/DateTimeUtils';

import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

function getStepperLoadingPane(): JSX.Element {
  return (
    <div>
      <h1>
        <Spinner animation="border" /> Loading state for content.
      </h1>
    </div>
  );
}

export default function ContentDetailsWithStepper(): JSX.Element {
  const {id} = useParams<{id: string}>();
  const [contentType, setContentType] = useState(null);
  const [contentPreviewURL, setContentPreviewURL] = useState(null);

  // Stage Times
  const [submittedAt, setSubmittedAt] = useState();
  const [hashedAt, setHashedAt] = useState();
  const [matchedAt, setMatchedAt] = useState();
  const [actionEvaluatedAt, setActionEvaluatedAt] = useState();
  const [actionPerformedAt, setActionPerformedAt] = useState();

  // Stage Details
  const [additionalFields, setAdditionalFields] = useState([]);
  const [hashResults, setHashResults] = useState({});
  const [matchResults, setMatchResults] = useState({});
  const [actionEvaluationResults, setActionEvaluationResults] = useState([]);
  const [actionPerformResults, setActionPerformResults] = useState([]);

  useEffect(() => {
    fetchContentPipelineProgress(id).then(pipelineProgress => {
      setContentType(pipelineProgress.content_type);
      setContentPreviewURL(pipelineProgress.content_preview_url);

      // Handle date times
      setSubmittedAt(
        pipelineProgress.submitted_at && toDate(pipelineProgress.submitted_at),
      );
      setHashedAt(
        pipelineProgress.hashed_at && toDate(pipelineProgress.hashed_at),
      );
      setMatchedAt(
        pipelineProgress.matched_at && toDate(pipelineProgress.matched_at),
      );
      setActionEvaluatedAt(
        pipelineProgress.action_evaluated_at &&
          toDate(pipelineProgress.action_evaluated_at),
      );
      setActionPerformedAt(
        pipelineProgress.action_performed_at &&
          toDate(pipelineProgress.action_performed_at),
      );
    });
  }, []);

  return (
    <FixedWidthCenterAlignedLayout title="Progress">
      <Row>
        <Col md={{span: 6}}>
          {contentPreviewURL ? (
            <ContentPreview
              contentId={id}
              contentType={ContentType.Photo}
              url={contentPreviewURL!}
            />
          ) : null}
        </Col>
        <Col md={{span: 6}}>
          {submittedAt === null ? (
            getStepperLoadingPane()
          ) : (
            <ContentProgressStepper
              submittedAt={submittedAt!}
              hashedAt={hashedAt}
              matchedAt={matchedAt}
              actionEvaluatedAt={actionEvaluatedAt}
              actionPerformedAt={actionPerformedAt}
            />
          )}
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}
